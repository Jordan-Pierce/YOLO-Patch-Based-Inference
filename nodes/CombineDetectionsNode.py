import cv2
import numpy as np

from elements.CropElement import CropElement
from nodes.MakeCropsDetectThem import MakeCropsDetectThem

class CombineDetectionsNode:
    # Класс, реализующий нарезку на кропы и прогон через сеть
    def __init__(
        self,
        element_crops: MakeCropsDetectThem,
        nms_iou=0.6
    ) -> None:
        self.conf_treshold = element_crops.conf
        self.crops = element_crops.crops  # List to store the CropElement objects
        if element_crops.resize_results:
            self.image = element_crops.crops[0].source_image_resized
        else:
            self.image = element_crops.crops[0].source_image
        self.nms_iou = nms_iou  # IoU treshold for NMS
        (
            self.detected_conf_list_full,
            self.detected_xyxy_list_full,
            self.detected_masks_list_full,
            self.detected_cls_list_full
        ) = self.combinate_detections(crops=self.crops)

        print(np.array(self.detected_conf_list_full).shape)
        print(np.array(self.detected_xyxy_list_full).shape)
        print(np.array(self.detected_masks_list_full).shape)
        print(np.array(self.detected_cls_list_full).shape)

        # Вызываем метод nms для фильтрации предсказаний
        self.filtered_indices = self.nms(
            self.detected_conf_list_full,
            self.detected_xyxy_list_full,
            self.nms_iou
        )

        # Применяем фильтрацию к спискам предсказаний
        self.filtered_confidences = [self.detected_conf_list_full[i] for i in self.filtered_indices]
        self.filtered_boxes = [self.detected_xyxy_list_full[i] for i in self.filtered_indices]
        self.filtered_classes = [self.detected_cls_list_full[i] for i in self.filtered_indices]

        if element_crops.segment:
            self.filtered_masks = [self.detected_masks_list_full[i] for i in self.filtered_indices]
        else:
            self.filtered_masks = []


        print(np.array(self.filtered_confidences).shape)
        print(np.array(self.filtered_boxes).shape)
        print(np.array(self.filtered_masks).shape)
        print(np.array(self.filtered_classes).shape)


        
    def combinate_detections(self, crops):
        detected_conf = []
        detected_xyxy = []
        detected_masks = []
        detected_cls = []

        for crop in crops:
            detected_conf.extend(crop.detected_conf)
            detected_xyxy.extend(crop.detected_xyxy_real)
            detected_masks.extend(crop.detected_masks_real)
            detected_cls.extend(crop.detected_cls)

        return detected_conf, detected_xyxy, detected_masks, detected_cls


    def nms(self, confidences, boxes, iou_threshold):
        # Преобразуем формат bbox'ов из xyxy в x, y, width, height
        bboxes = [[box[0], box[1], box[2] - box[0], box[3] - box[1]] for box in boxes]

        # Вызываем функцию NMSBoxes
        picked_indices = cv2.dnn.NMSBoxes(bboxes, confidences, self.conf_treshold, iou_threshold)

        # Выдаем индексы отфильтрованных предсказаний
        return picked_indices