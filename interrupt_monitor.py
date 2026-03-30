"""
ESC 键中断检测模块
仅支持 Windows 系统
"""
import threading
import time

# 用于检测 ESC 打断的标志
interrupt_flag = False


def check_esc_interrupt():
    """
    在后台检测 ESC 键（仅 Windows）
    """
    global interrupt_flag
    try:
        import msvcrt
        while not interrupt_flag:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b'\x1b':  # ESC key
                    interrupt_flag = True
                    print("\n[检测到 ESC 键，正在中断...]")
                    break
            time.sleep(0.1)
    except ImportError:
        # 非 Windows 系统，无法检测 ESC
        pass


def start_interrupt_monitor():
    """
    启动中断检测线程
    """
    global interrupt_flag
    interrupt_flag = False
    thread = threading.Thread(target=check_esc_interrupt, daemon=True)
    thread.start()


def stop_interrupt_monitor():
    """
    停止中断检测
    """
    global interrupt_flag
    interrupt_flag = True


def is_interrupted() -> bool:
    """
    检查是否被中断
    """
    global interrupt_flag
    return interrupt_flag
