import time      
import random   

def run_virtual_fpga(port_path):
  
    print(f"--- 虚拟FPGA已启动 ---")
    print(f"目标端口: {port_path}")
    print("将每2秒生成并发送一次温湿度数据...")
    print("按 Ctrl+C 停止运行。")

    try:
        with open(port_path, 'w') as serial_port:
            while True:
                temp = round(random.uniform(22.0, 28.0), 1)
                humidity = round(random.uniform(40.0, 65.0), 1)
                data_string = f"temp:{temp},humi:{humidity}\n"
                serial_port.write(data_string)
                serial_port.flush()
                print(f"已发送 -> {data_string.strip()}")
                time.sleep(2)

    except FileNotFoundError:
        print(f"\n[错误!] 找不到虚拟串口 '{port_path}'。")
        print("请确保你已经使用socat等工具创建了虚拟串口对。")
    except KeyboardInterrupt:
        print("\n--- 虚拟FPGA已停止 ---")
    except Exception as e:
        print(f"\n[发生未知错误!] {e}")

if __name__ == "__main__":
    
    # 命令行用法示例: python3 mock_fpga.py /dev/pts/2
    MOCK_SERIAL_PORT = "/dev/pts/6"#根据socat显示接口来更改
    run_virtual_fpga(MOCK_SERIAL_PORT)