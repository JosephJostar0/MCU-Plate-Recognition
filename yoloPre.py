from ultralytics.yolo.engine.predictor import BasePredictor
from ultralytics.yolo.engine.results import Results
from ultralytics.yolo.utils import DEFAULT_CFG, LOGGER, SETTINGS, callbacks, ops
from ultralytics.yolo.utils.plotting import Annotator, colors, save_one_box
from ultralytics.yolo.utils.torch_utils import smart_inference_mode
from ultralytics.yolo.utils.files import increment_path
from ultralytics.yolo.utils.checks import check_imshow
from ultralytics.yolo.cfg import get_cfg
import queue

from lprr import CHARS
from collections import defaultdict
from pathlib import Path
from lprr.plate import de_lpr, dr_plate
import numpy as np
import time
import torch
import cv2

waitQueue = queue.Queue()
runFlag = True


class YoloPredictor(BasePredictor):
    global waitQueue, runFlag

    def __init__(self, cfg=DEFAULT_CFG, overrides=None):

        # 多重继承
        super(YoloPredictor, self).__init__()

        self.carNumList = []

        # get_cfg() 函数可以从配置文件中获取参数 【使用 self.args 保存最终的配置】
        self.args = get_cfg(cfg, overrides)

        project = self.args.project or Path(
            SETTINGS['runs_dir']) / self.args.task
        name = f'{self.args.mode}'
        self.save_dir = increment_path(
            Path(project) / name, exist_ok=self.args.exist_ok)

        self.done_warmup = False
        if self.args.show:
            self.args.show = check_imshow(warn=True)

        # 我定义的属性
        self.iscamera = 0
        self.capture_frame = None

        # GUI args
        self.used_model_name = None  # The detection model name to use
        self.new_model_name = None  # Models that change in real time
        self.source = ''  # input source
        self.stop_dtc = False  # Termination detection
        self.continue_dtc = True  # pause
        self.save_res = False  # Save test results
        self.save_txt = False  # save label(txt) file
        self.iou_thres = 0.45  # iou
        self.conf_thres = 0.25  # conf
        self.speed_thres = 10  # delay, ms
        self.labels_dict = {}  # return a dictionary of results
        self.progress_value = 0  # progress bar

        # Usable if setup is done
        self.model = None
        self.data = self.args.data  # data_dict
        self.imgsz = None
        self.device = None
        self.dataset = None
        self.vid_path, self.vid_writer = None, None
        self.annotator = None
        self.data_path = None
        self.source_type = None
        self.batch = None
        self.callbacks = defaultdict(
            list, callbacks.default_callbacks)  # add callbacks
        callbacks.add_integration_callbacks(self)

    def beforeRun(self, modeName: str = r'.\models\car.pt'):
        self.new_model_name = modeName
        self.save_res = True
        self.save_txt = True

        if self.args.verbose:
            LOGGER.info('')

        # print('加载模型')
        if not self.model:
            self.setup_model(self.new_model_name)
            self.used_model_name = self.new_model_name
            if self.save_res or self.save_txt:
                (self.save_dir / 'labels' if self.save_txt else self.save_dir).mkdir(
                    parents=True, exist_ok=True)

    # main for detect
    @smart_inference_mode()
    def run(self):
        global runFlag
        try:
            while runFlag:
                self.source = waitQueue.get(timeout=3)

                # set source  [视频资源]
                # print('设置资源模式')
                self.setup_source(
                    self.source if self.source is not None else self.args.source)

                if not self.done_warmup:
                    # 调用模型的 warmup 函数，其中 imgsz 参数为输入图像的大小
                    # 如果模型使用 PyTorch，imgsz 参数应为 [batch_size, channels, height, width]
                    # 如果模型使用 Triton，imgsz 参数应为 [height, width, channels, batch_size]
                    self.model.warmup(imgsz=(
                        1 if self.model.pt or self.model.triton else self.dataset.bs, 3, *self.imgsz))
                    # 将 done_warmup 标记为 True，以标记模型已经热身过
                    self.done_warmup = True
                self.seen, self.windows, self.dt, self.batch = 0, [
                ], (ops.Profile(), ops.Profile(), ops.Profile()), None
                # 创建名为 dt 的实例变量，用于存储一个元组，并将其初始化为包含三个对象 ops.Profile() 的元组。
                # ops.Profile() 是指从 ops 模块中导入名为 Profile() 的对象。

                count = 0  # run location frame
                start_time = time.time()  # used to calculate the frame rate
                batch = iter(self.dataset)
                while True:
                    # Termination detection  【终止检测】
                    if self.stop_dtc:
                        # 释放CV2视频写入器
                        if isinstance(self.vid_writer[-1], cv2.VideoWriter):
                            # release final video writer
                            self.vid_writer[-1].release()
                        # self.yolo2main_status_msg.emit('Detection terminated!')
                        break

                    # Change the model midway 【切换model】  如果不相等，则执行 setup_model() 方法设置新的模型
                    if self.used_model_name != self.new_model_name:
                        # self.yolo2main_status_msg.emit('Change Model...')
                        self.setup_model(self.new_model_name)
                        self.used_model_name = self.new_model_name

                    # pause switch  用于控制程序的暂停和继续
                    if self.continue_dtc:
                        # time.sleep(0.001)
                        # self.yolo2main_status_msg.emit('Detecting...')
                        batch = next(self.dataset)  # next data

                        self.batch = batch
                        path, im, im0s, vid_cap, s = batch
                        visualize = increment_path(self.save_dir / Path(path).stem,
                                                   mkdir=True) if self.args.visualize else False

                        # Calculation completion and frame rate (to be optimized)
                        count += 1  # frame count +1
                        if vid_cap:
                            all_count = vid_cap.get(
                                cv2.CAP_PROP_FRAME_COUNT)  # total frames
                        else:
                            all_count = 1
                        self.progress_value = int(
                            count / all_count * 1000)  # progress bar(0~1000)
                        if count % 5 == 0 and count >= 5:  # Calculate the frame rate every 5 frames
                            # self.yolo2main_fps.emit(
                            # str(int(5 / (time.time() - start_time))))
                            start_time = time.time()

                        # preprocess
                        # self.dt 包含了三个 DetectorTime 类型的对象，表示预处理、推理和后处理所花费的时间

                        # 使用 with 语句记录下下一行代码所花费的时间，self.dt[0] 表示记录预处理操作所花费的时间。
                        with self.dt[0]:
                            # 调用 self.preprocess 方法对图像进行处理，并将处理后的图像赋值给 im 变量。
                            im = self.preprocess(im)
                            # 如果 im 的维度为 3（RGB 图像），则表示这是一张单张图像，需要将其扩展成 4 维，加上 batch 维度。
                            if len(im.shape) == 3:
                                im = im[None]  # expand for batch dim  扩大批量调暗
                        # inference
                        with self.dt[1]:
                            # 调用模型对图像进行推理，并将结果赋值给 preds 变量。
                            preds = self.model(
                                im, augment=self.args.augment, visualize=visualize)
                        # postprocess
                        with self.dt[2]:
                            # 调用 self.postprocess 方法对推理结果进行后处理，并将结果保存到 self.results 变量中。
                            # 其中 preds 是模型的预测结果，im 是模型输入的图像，而 im0s 是原始图像的大小。
                            self.results = self.postprocess(preds, im, im0s)

                        # visualize, save, write results
                        n = len(im)  # To be improved: support multiple img
                        for i in range(n):
                            self.results[i].speed = {
                                'preprocess': self.dt[0].dt * 1E3 / n,
                                'inference': self.dt[1].dt * 1E3 / n,
                                'postprocess': self.dt[2].dt * 1E3 / n}
                            p, im0 = (path[i], im0s[i].copy()) if self.source_type.webcam or self.source_type.from_img \
                                else (path, im0s.copy())

                            p = Path(p)  # the source dir

                            # s:::   video 1/1 (6/6557) 'path':
                            # must, to get boxs\labels
                            # labels   /// original :s +=
                            label_str = self.write_results(
                                i, self.results, (p, im, im0))

                            # labels and nums dict
                            class_nums = 0
                            target_nums = 0
                            self.labels_dict = {}
                            if 'no detections' in label_str:
                                pass
                            else:
                                for ii in label_str.split(',')[:-1]:
                                    nums, label_name = ii.split('~')
                                    self.labels_dict[label_name] = int(nums)
                                    target_nums += int(nums)
                                    class_nums += 1

                            # save img or video result
                            if self.save_res:
                                self.save_preds(vid_cap, i, str(
                                    self.save_dir / p.name))

                    # Detection completed
                    if count + 1 >= all_count:
                        if isinstance(self.vid_writer[-1], cv2.VideoWriter):
                            # release final video writer
                            self.vid_writer[-1].release()
                        # self.yolo2main_status_msg.emit('Detection completed')
                        break
        except queue.Empty:
            print('yoloPredictor: queue.Empty')
            runFlag = False
            return
        except Exception as e:
            print(e)
            # self.yolo2main_status_msg.emit('%s' % e)

    def get_annotator(self, img):
        return Annotator(img, line_width=self.args.line_thickness, example=str(self.model.names))

    def preprocess(self, img):
        img = torch.from_numpy(img).to(self.model.device)
        img = img.half() if self.model.fp16 else img.float()  # uint8 to fp16/32
        img /= 255  # 0 - 255 to 0.0 - 1.0
        return img

    def postprocess(self, preds, img, orig_img):
        # important
        preds = ops.non_max_suppression(preds,
                                        self.conf_thres,
                                        self.iou_thres,
                                        agnostic=self.args.agnostic_nms,
                                        max_det=self.args.max_det,
                                        classes=self.args.classes)

        results = []
        for i, pred in enumerate(preds):
            orig_img = orig_img[i] if isinstance(orig_img, list) else orig_img
            shape = orig_img.shape
            pred[:, :4] = ops.scale_boxes(
                img.shape[2:], pred[:, :4], shape).round()
            path, _, _, _, _ = self.batch
            img_path = path[i] if isinstance(path, list) else path
            results.append(Results(orig_img=orig_img, path=img_path,
                           names=self.model.names, boxes=pred))
        return results

    # 画结果
    def write_results(self, idx, results, batch):
        # idx 是一个整数，用于指定批处理中的某个图像；
        # results 是一个列表，其中包含在模型中对 batch 执行前向传递的结果；
        # batch 是模型输入的一个批处理张量，它由三个元素组成：p，im 和 im0。

        # 将元组 batch 中三个变量解包存储到 p、im 和 im0 中。
        p, im, im0 = batch
        log_string = ''

        # 用于判断输入图像的形状（shape）是否为 3D，如果是则在前面添加一个新的维度，以表示批处理。这是一种处理不同大小的输入图像的常见方法。
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        self.seen += 1

        # 使用 if/else 语句设置变量 imc，该变量存储输入图像的一个副本。
        # 如果参数 save_crop（在 self.args 中）为真，则存储裁剪的图像，否则存储原始图像。
        imc = im0.copy() if self.args.save_crop else im0

        # 检查输入数据是否来自网络摄像头或图像文件
        if self.source_type.webcam or self.source_type.from_img:  # batch_size >= 1         # attention
            log_string += f'{idx}: '
            frame = self.dataset.count
        else:
            frame = getattr(self.dataset, 'frame', 0)
        self.data_path = p
        self.txt_path = str(self.save_dir / 'labels' / p.stem) + \
            ('' if self.dataset.mode == 'image' else f'_{frame}')
        # log_string += '%gx%g ' % im.shape[2:]         # !!! don't add img size~
        self.annotator = self.get_annotator(im0)

        # 统计检测到的目标数量和种类的段落
        det = results[idx].boxes  # TODO: make boxes inherit from tensors

        if len(det) == 0:
            return f'{log_string}(no detections), '  # if no, send this~~

        # 添加当前目标数量和名称到日志字符串
        # 【det.cls.unique() 方法返回了 det.cls 列中的所有唯一值】
        for c in det.cls.unique():
            # det.cls == c 这个条件判断表达式会返回一个由布尔值组成的数组
            n = (det.cls == c).sum()  # detections per class

            # it only recognizes license-plates and records the total number of license-plates
            if (self.model.names[int(c)] == 'license-plate'):
                # {'s' * (n > 1)}, "   # don't add 's'
                log_string = f"{n}~{self.model.names[int(c)]},"

        # now log_string is the classes 👆
        # print(log_string)

        # write & save & draw
        for d in reversed(det):

            cls, conf = d.cls.squeeze(), d.conf.squeeze()

            # 获取类别  get category
            c = int(cls)  # integer class
            name = f'id:{int(d.id.item())} {self.model.names[c]}' if d.id is not None else self.model.names[c]

            # 如果不是车牌，则跳过！
            # if there is not a license-plate, jump it
            if (name != 'license-plate'):
                continue

            # 画车牌 draw a license plate
            plate = de_lpr(d.xyxy.squeeze(), im0)
            plate = np.array(plate)
            car_number_laber = ""
            for i in range(0, plate.shape[1]):
                b = CHARS[plate[0][i]]
                car_number_laber += b

            def count_non_lowercase_chars(input_string):
                count = 0
                for char in input_string:
                    if not char.islower():
                        count += 1
                return count

            numStem = count_non_lowercase_chars(car_number_laber)
            if len(car_number_laber) < 7 or numStem < 6 or numStem > 7:
                continue

            replaceDic = {
                '8': 'B', '0': 'D', '1': 'I',
            }
            letter = car_number_laber[-numStem-1]
            if letter in replaceDic.keys():
                car_number_laber = car_number_laber[:-numStem-1] + \
                    replaceDic[letter] + car_number_laber[-numStem:]

            self.carNumList.append(car_number_laber[-numStem:])

            def find_most_common_string(strings: list):
                frequency_dict = {}
                for s in strings:
                    frequency_dict[s] = frequency_dict.get(s, 0) + 1
                mostCommonStr = max(frequency_dict, key=frequency_dict.get)
                return mostCommonStr

            if len(self.carNumList) == 8:
                mostNum = find_most_common_string(self.carNumList)
                self.carNumList.clear()
                print(mostNum, end=', ')
                print(count_non_lowercase_chars(mostNum) == 7)

            if self.save_txt:  # Write to file 写入文本文件

                line = (cls, *(d.xywhn.view(-1).tolist()), conf) \
                    if self.args.save_conf else (cls, *(d.xywhn.view(-1).tolist()))  # label format
                with open(f'{self.txt_path}.txt', 'a') as f:
                    f.write(('%g ' * len(line)).rstrip() % line + '\n')

            # 检测结果绘制到图像上，并显示出来。
            # Add bbox to image(must)
            if self.save_res or self.args.save_crop or self.args.show or True:

                # 如果 self.args.hide_labels = True，则为 None
                # 否则 (name if self.args.hide_conf else f'{name} {conf:.2f}')
                # 如果 self.args.hide_conf = True，则为 name
                # 否则 f'{name} {conf:.2f}'
                self.annotator.box_label(
                    d.xyxy.squeeze(), car_number_laber, color=colors(c, True))

                # 原标签 original label
                # label = None if self.args.hide_labels else (name if self.args.hide_conf else f'{name} {conf:.2f}')

            # 将画在图像上的边界框区域保存为一个单独的图像或者视频文件
            if self.args.save_crop:
                save_one_box(d.xyxy,
                             imc,
                             file=self.save_dir / 'crops' /
                             self.model.model.names[c] /
                             f'{self.data_path.stem}.jpg',
                             BGR=True)

        return log_string
