"""
========================================
Interrupt Monitor - ESC键中断检测模块
========================================
功能: 检测用户按下的ESC键来中断AI执行过程
仅支持Windows系统
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════

import threading
import time

# ═══════════════════════════════════════════════════════════════
# 全局中断标志
# ═══════════════════════════════════════════════════════════════

# 用于检测ESC打断的标志
# 当用户按下ESC时设为True
interrupt_flag = False


# ═══════════════════════════════════════════════════════════════
# 中断检测函数
# ═══════════════════════════════════════════════════════════════


def check_esc_interrupt():
    """
    在后台线程中检测ESC键（仅Windows）

    使用msvcrt模块监听键盘输入
    当检测到ESC键（\x1b）时设置interrupt_flag为True

    注意: 此函数在独立线程中运行
    """
    global interrupt_flag
    try:
        import msvcrt

        # 循环检测直到中断标志被设置
        while not interrupt_flag:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\x1b":  # ESC键的字节码
                    interrupt_flag = True
                    print("\n[检测到 ESC 键，正在中断...]")
                    break
            # 休眠一小段时间，避免CPU占用过高
            time.sleep(0.1)
    except ImportError:
        # 非Windows系统，无法检测ESC
        pass


# ═══════════════════════════════════════════════════════════════
# 中断监控线程管理函数
# ═══════════════════════════════════════════════════════════════


def start_interrupt_monitor():
    """
    启动中断检测线程

    创建并启动一个守护线程来监听ESC键
    """
    global interrupt_flag
    interrupt_flag = False  # 重置标志
    thread = threading.Thread(target=check_esc_interrupt, daemon=True)
    thread.start()


def stop_interrupt_monitor():
    """
    停止中断检测

    通过设置interrupt_flag为True来停止检测
    """
    global interrupt_flag
    interrupt_flag = True


def is_interrupted() -> bool:
    """
    检查是否被中断

    返回:
        True表示用户按下了ESC键希望中断执行
    """
    global interrupt_flag
    return interrupt_flag
