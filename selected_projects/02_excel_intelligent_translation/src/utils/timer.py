import sys
import time
import threading

def live_timer(stop_event: threading.Event, prefix_msg: str, start_time: float):
    """后台计时器线程，用于在终端实时刷新耗时，精度 0.01s，刷新率 20Hz"""
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        sys.stdout.write(f"\r\033[K{prefix_msg} [{elapsed:.2f}s]")
        sys.stdout.flush()
        # 将 sleep 时间缩短到 0.05 秒，确保终端以大约 20fps 的刷新率更新，消除卡顿感
        time.sleep(0.05)
    # 停止后换行
    sys.stdout.write("\n")
    sys.stdout.flush()

class StageTimer:
    """阶段计时器上下文管理器"""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = 0.0
        self.end_time = 0.0
        self.stop_event = threading.Event()
        self.thread = None

    def __enter__(self):
        self.start_time = time.time()
        self.thread = threading.Thread(
            target=live_timer, 
            args=(self.stop_event, self.stage_name, self.start_time),
            daemon=True
        )
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        print(f"   -> 完成耗时: {elapsed:.2f}s")
