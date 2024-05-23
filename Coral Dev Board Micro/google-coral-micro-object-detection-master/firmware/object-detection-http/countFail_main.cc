#include <cstdio>
#include <vector>
#include <cmath>
#include <map>

#include "libs/base/filesystem.h"
#include "libs/base/http_server.h"
#include "libs/base/led.h"
#include "libs/base/strings.h"
#include "libs/base/utils.h"
#include "libs/camera/camera.h"
#include "libs/libjpeg/jpeg.h"
#include "libs/tensorflow/detection.h"
#include "libs/tensorflow/utils.h"
#include "libs/tpu/edgetpu_manager.h"
#include "libs/tpu/edgetpu_op.h"
#include "third_party/freertos_kernel/include/FreeRTOS.h"
#include "third_party/freertos_kernel/include/task.h"
#include "third_party/freertos_kernel/include/semphr.h"
#include "third_party/tflite-micro/tensorflow/lite/micro/micro_error_reporter.h"
#include "third_party/tflite-micro/tensorflow/lite/micro/micro_interpreter.h"
#include "third_party/tflite-micro/tensorflow/lite/micro/micro_mutable_op_resolver.h"

#include "metadata.hpp"

#define ENABLE_HTTP_SERVER 1
#define DEBUG 1

namespace coralmicro {
namespace {

// Image result struct
typedef struct {
  std::string info;
  std::vector<uint8_t> *jpeg;
} ImgResult;

// Bounding box struct
typedef struct {
  float id;
  float score;
  float ymin;
  float xmin;
  float ymax;
  float xmax;
} BBox;

// Camera settings
constexpr auto camRotation = CameraRotation::k270; // Default: CameraRotation::k0

// Globals
constexpr char kIndexFileName[] = "/index.html";
constexpr char kCameraStreamUrlPrefix[] = "/camera_stream";
constexpr char kBoundingBoxPrefix[] = "/bboxes";
constexpr char kModelPath[] =
    "/model_int8_edgetpu.tflite";
constexpr int kTensorArenaSize = 8 * 1024 * 1024;
STATIC_TENSOR_ARENA_IN_SDRAM(tensor_arena, kTensorArenaSize);
static std::vector<uint8_t> *img_ptr;
static SemaphoreHandle_t img_mutex;
static SemaphoreHandle_t bbox_mutex;
static int img_width;
static int img_height;
static constexpr float score_threshold = 0.5f;
static constexpr float iou_threshold = 0.3f;
static constexpr size_t max_bboxes = 5;
static constexpr unsigned int bbox_buf_size = 100 + (max_bboxes * 200) + 1;
static char bbox_buf[bbox_buf_size];

// Object counts per class
static std::map<int, int> object_counts;

// Copy of image data for HTTP server
#if ENABLE_HTTP_SERVER
static std::vector<uint8_t> *img_copy;
#endif

/*******************************************************************************
 * Functions
 */

void Blink(unsigned int num, unsigned int delay_ms);
bool CalculateAnchorBox(unsigned int idx, float *anchor);
float CalculateIOU(BBox *bbox1, BBox *bbox2);

#if ENABLE_HTTP_SERVER
/**
 * Handle HTTP requests
 */
HttpServer::Content UriHandler(const char* uri) {

  // Give client main page
  if (StrEndsWith(uri, "index.shtml") ||
      StrEndsWith(uri, "coral_micro_camera.html")) {
    return std::string(kIndexFileName);

  // Give client compressed image data
  } else if (StrEndsWith(uri, kCameraStreamUrlPrefix)) {

    // Read image from shared memory and compress to JPG
    std::vector<uint8_t> jpeg;
    if (xSemaphoreTake(img_mutex, portMAX_DELAY) == pdTRUE) {
      JpegCompressRgb(
        img_copy->data(), 
        img_width, 
        img_height, 
        75,         // Quality
        &jpeg
      );
      xSemaphoreGive(img_mutex);
    }

    return jpeg;

  // Give client bounding box info
  } else if (StrEndsWith(uri, kBoundingBoxPrefix)) {

    // Read bounding box info from shared memory and convert to vector of bytes
    char bbox_info_copy[bbox_buf_size];
    std::vector<uint8_t> bbox_info_bytes;
    if (xSemaphoreTake(bbox_mutex, portMAX_DELAY) == pdTRUE) {
      std::strcpy(bbox_info_copy, bbox_buf);
      bbox_info_bytes.assign(
        bbox_info_copy, 
        bbox_info_copy + std::strlen(bbox_info_copy)
      );
      xSemaphoreGive(bbox_mutex);
    }

    // TODO: Figure out the multi-request or race condition bug that is causing
    // the bbox_info_bytes to be corrupted. The workaround is to have the
    // client timeout if it doesn't get a response in some amount of time.

    return bbox_info_bytes;
  }

  return {};
}
#endif

/**
 * Loop forever taking images from the camera and performing inference
 */
[[noreturn]] void InferenceTask(void* param) {

  // Used for calculating FPS
  unsigned long dtime;
  unsigned long timestamp;
  unsigned long timestamp_prev = xTaskGetTickCount() * 
    (1000 / configTICK_RATE_HZ);

  // x_center, y_center, w, h
  float anchor[4] = {0.0f, 0.0f, 0.0f, 0.0f};

  // Load model
  std::vector<uint8_t> model;
  if (!LfsReadFile(kModelPath, &model)) {
    printf("ERROR: Failed to load %s\r\n", kModelPath);
    vTaskSuspend(nullptr);
  }

  // Initialize TPU
  auto tpu_context = EdgeTpuManager::GetSingleton()->OpenDevice();
  if (!tpu_context) {
    printf("ERROR: Failed to get EdgeTpu context\r\n");
    vTaskSuspend(nullptr);
  }

  // Initialize ops
  tflite::MicroErrorReporter error_reporter;
  tflite::MicroMutableOpResolver<3> resolver;
  resolver.AddDequantize();
  resolver.AddDetectionPostprocess();
  resolver.AddCustom(kCustomOp, RegisterCustomOp());

  // Initialize TFLM interpreter for inference
  tflite::MicroInterpreter interpreter(
    tflite::GetModel(model.data()), 
    resolver,
    tensor_arena, 
    kTensorArenaSize,
    &error_reporter
  );
  if (interpreter.AllocateTensors() != kTfLiteOk) {
    printf("ERROR: AllocateTensors() failed\r\n");
    vTaskSuspend(nullptr);
  }

  // Check model input tensor size
  if (interpreter.inputs().size() != 1) {
    printf("ERROR: Model must have only one input tensor\r\n");
    vTaskSuspend(nullptr);
  }

  // Configure model inputs and outputs
  auto* input_tensor = interpreter.input_tensor(0);
  img_height = input_tensor->dims->data[1];
  img_width = input_tensor->dims->data[2];
  img_ptr = new std::vector<uint8>(img_height * img_width * 
    CameraFormatBpp(CameraFormat::kRgb));
  std::vector<tensorflow::Object> results;
#if ENABLE_HTTP_SERVER
    img_copy = new std::vector<uint8_t>(img_ptr->size());
#endif

  // Get output tensor shapes
  TfLiteTensor* tensor_bboxes = interpreter.output_tensor(0);
  TfLiteTensor* tensor_scores = interpreter.output_tensor(1);
  unsigned int num_boxes = tensor_bboxes->dims->data[1];
  unsigned int num_coords = tensor_bboxes->dims->data[2];
  unsigned int num_classes = tensor_scores->dims->data[2];

  // Get quantization parameters
  const float input_scale = input_tensor->params.scale;
  const int input_zero_point = input_tensor->params.zero_point;
  const float locs_scale = tensor_bboxes->params.scale;
  const int locs_zero_point = tensor_bboxes->params.zero_point;
  const float scores_scale = tensor_scores->params.scale;
  const int scores_zero_point = tensor_scores->params.zero_point;

  // Convert threshold to fixed point
  uint8_t score_threshold_quantized = 
    static_cast<uint8_t>(score_threshold * 256);

  // Print input/output details
#if DEBUG
  printf("num_boxes: %d\r\n", num_boxes);
  printf("num_coords: %d\r\n", num_coords);
  printf("num_classes: %d\r\n", num_classes);
  printf("bytes in tensor_bboxes: %d\r\n", tensor_bboxes->bytes);
  if (tensor_scores->data.data == nullptr) {
    printf("tensor_scores.data is empty!\r\n");
  }
  printf("input_scale: %f\r\n", input_scale);
  printf("input_zero_point: %d\r\n", input_zero_point);
  printf("locs_scale: %f\r\n", locs_scale);
  printf("locs_zero_point: %d\r\n", locs_zero_point);
  printf("scores_scale: %f\r\n", scores_scale);
  printf("scores_zero_point: %d\r\n", scores_zero_point);
  printf("score_threshold_quantized: %d\r\n", score_threshold_quantized);
#endif

  // Do forever
  while (true) {

    std::vector<std::vector<float>> bbox_list;

    // Capture image
    CameraFrameFormat fmt = {CameraFormat::kRgb, img_width, img_height};
    CameraFrameBufferMode mode = CameraFrameBufferMode::kContinuous;
    auto* cam = Camera::GetSingleton();
    cam->SetPower(true);
    cam->SetFrameFormat(fmt);
    cam->SetGain(0); // minimum gain
    cam->SetFrameBufferMode(mode);
    cam->Start();

    // Save image to shared memory
    cam->GetFrame(img_ptr->data());
#if ENABLE_HTTP_SERVER
    if (xSemaphoreTake(img_mutex, portMAX_DELAY) == pdTRUE) {
      std::memcpy(img_copy->data(), img_ptr->data(), img_ptr->size());
      xSemaphoreGive(img_mutex);
    }
#endif

    // Quantize input from int8 to uint8
    for (unsigned int i = 0; i < img_ptr->size(); ++i) {
      input_tensor->data.uint8[i] = static_cast<uint8_t>(
        (img_ptr->data()[i] - input_zero_point) * input_scale);
    }

    // Perform inference
    if (interpreter.Invoke() != kTfLiteOk) {
      printf("ERROR: Invoke() failed\r\n");
      vTaskSuspend(nullptr);
    }

    // Get bounding boxes and scores
    for (unsigned int i = 0; i < num_boxes; ++i) {
      float score = 
        ((tensor_scores->data.uint8[i] - scores_zero_point) * scores_scale);
      if (score > score_threshold) {
        std::vector<float> bbox;
        bbox.push_back(tensor_scores->data.uint8[i * num_classes + 1]);
        bbox.push_back(score);
        for (unsigned int j = 0; j < num_coords; ++j) {
          bbox.push_back((tensor_bboxes->data.uint8[(i * num_coords) + j] - 
            locs_zero_point) * locs_scale);
        }
        bbox_list.push_back(bbox);
      }
    }

    // Process bounding boxes
    for (unsigned int i = 0; i < bbox_list.size(); ++i) {
      BBox bbox = {bbox_list[i][0], bbox_list[i][1], bbox_list[i][2], bbox_list[i][3], bbox_list[i][4], bbox_list[i][5]};

      // Check if this bounding box has already been counted
      if (!IsAlreadyCounted(bbox, counted_objects, iou_threshold)) {
        // Add to counted objects and increment count for the specific class
        counted_objects.push_back({static_cast<int>(bbox.id), bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax});
        object_counts[static_cast<int>(bbox.id)]++;
        
        // Optional: Remove old counted objects based on a frame/time threshold to avoid memory overflow
        // This is a simplistic example of clearing the vector periodically
        if (counted_objects.size() > 1000) {
          counted_objects.clear();
        }
      }
    }

    // Print the current counts of classifications per class
    for (const auto &pair : object_counts) {
      printf("Class %d: %d objects\r\n", pair.first, pair.second);
    }

    // Calculate FPS
    timestamp = xTaskGetTickCount() * (1000 / configTICK_RATE_HZ);
    dtime = timestamp - timestamp_prev;
    timestamp_prev = timestamp;
    printf("FPS: %.2f\r\n", 1000.0f / static_cast<float>(dtime));
  }
}

/**
 * Initialize the system and create the inference task
 */
[[noreturn]] void MainTask(void* param) {

  // Blink LED to indicate initialization
  Blink(5, 100);

  // Initialize the camera
  if (!Camera::GetSingleton()->Initialize(camRotation)) {
    printf("ERROR: Camera initialization failed\r\n");
    vTaskSuspend(nullptr);
  }

  // Create the image and bounding box mutexes
  img_mutex = xSemaphoreCreateMutex();
  bbox_mutex = xSemaphoreCreateMutex();

#if ENABLE_HTTP_SERVER
  // Initialize the HTTP server
  HttpServer::GetSingleton()->SetUriHandler(UriHandler);
  HttpServer::GetSingleton()->Start();
#endif

  // Create the inference task
  xTaskCreate(
    InferenceTask,
    "InferenceTask",
    configMINIMAL_STACK_SIZE + 1024,
    nullptr,
    tskIDLE_PRIORITY + 1,
    nullptr
  );

  // Suspend the main task
  vTaskSuspend(nullptr);
}

/**
 * Blink the LED
 */
void Blink(unsigned int num, unsigned int delay_ms) {
  for (unsigned int i = 0; i < num; ++i) {
    Led::GetSingleton()->Set(Led::Color::kYellow);
    vTaskDelay(delay_ms / portTICK_PERIOD_MS);
    Led::GetSingleton()->Set(Led::Color::kOff);
    vTaskDelay(delay_ms / portTICK_PERIOD_MS);
  }
}

/**
 * Calculate anchor box coordinates
 */
bool CalculateAnchorBox(unsigned int idx, float *anchor) {

  if (idx >= metadata_anchors_size) return false;

  const float *anchor_ptr = &metadata_anchors[idx * metadata_anchors_width];
  anchor[0] = anchor_ptr[0];
  anchor[1] = anchor_ptr[1];
  anchor[2] = anchor_ptr[2];
  anchor[3] = anchor_ptr[3];

  return true;
}

/**
 * Calculate intersection-over-union of two bounding boxes
 */
float CalculateIOU(BBox *bbox1, BBox *bbox2) {

  float x_min_inter = std::max(bbox1->xmin, bbox2->xmin);
  float y_min_inter = std::max(bbox1->ymin, bbox2->ymin);
  float x_max_inter = std::min(bbox1->xmax, bbox2->xmax);
  float y_max_inter = std::min(bbox1->ymax, bbox2->ymax);

  float inter_width = std::max(0.0f, x_max_inter - x_min_inter);
  float inter_height = std::max(0.0f, y_max_inter - y_min_inter);
  float inter_area = inter_width * inter_height;

  float bbox1_area = (bbox1->xmax - bbox1->xmin) * (bbox1->ymax - bbox1->ymin);
  float bbox2_area = (bbox2->xmax - bbox2->xmin) * (bbox2->ymax - bbox2->ymin);

  return inter_area / (bbox1_area + bbox2_area - inter_area);
}

} // namespace
} // namespace coralmicro

/**
 * Main entry point
 */
int main() {
  coralmicro::MainTask(nullptr);
  return 0;
}
