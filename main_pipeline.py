import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options # 用于无头模式
import serial
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np




def fetch_weather(city_code: str):
    url = f'https://weather.cma.cn/web/weather/{city_code}.html' 
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver_path = '/usr/local/bin/chromedriver'
    #service = Service(executable_path=driver_path) 
    driver = None
    try:
        driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
        print("浏览器已启动(无头模式)")
        driver.get(url)
        print(f"正在访问: {url}")
        print("等待动态数据加载...")
        time.sleep(10)
        print("数据加载完成，正在获取页面源码...")
        html_content = driver.page_source 
        return html_content    
    except WebDriverException as e:
        print(f"浏览器驱动或访问时出错: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            print("浏览器已关闭。")
        
#def fetch_weather(city_code:str):
    url=f'https://weather.cma.cn/web/weather/{city_code}.html'
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0'}
    try:
        response=requests.get(url,headers=headers,timeout=10)
        response.raise_for_status()
        response.encoding='utf-8'
        return response.text
    except RequestException as e:
        print(f"获取网页信息失败，错误信息：{e}")
        return None
    
def parse_weather(html_content):
    if html_content is None:
        return  None
    try:
        soup=BeautifulSoup(html_content,'html.parser')
        weather_data={}
        condition_tag=soup.find('div',class_='day-item dayicon').find_next_sibling('div')
        if condition_tag:
            weather_data['天气']=condition_tag.get_text().strip()
        else:
            print("未找到天气情况标签(class=day-item dayicon)")
            weather_data['天气']='未知'
        temp_tag=soup.find('div',id='city_real_temp').find('span',id='temperature')  #.find('div',id_='city_real_temp')
        if temp_tag:
            weather_data['温度']=temp_tag.get_text()
        else:
            print("未找到温度标签(id=temperature)")
            weather_data['温度']='未知'
        humi_tag=soup.find('span',id='humidity')  #.find('i',class_='iconfont icon-humidity')
        if humi_tag:
            weather_data['相对湿度']=humi_tag.get_text()
        else:
            print("未找到湿度标签(id=humidity)")
            weather_data['相对湿度']='未知'
        return weather_data
    except Exception as e:
        print(f"解析天气数据时发生未知错误：{e}")
        return None



def save_to_csv(data_list:list,filename:str):
    df=pd.DataFrame(data_list)
    df.to_csv(filename,index=False,encoding='utf-8-sig')
    print(f"数据已经成功保存到文件：{filename}")

def receive_fpga_data():
    serial_port='/dev/pts/7'
    baud_rate=9600
    print(f"步骤1：正在尝试从串口{serial_port}接收数据")
    ser=None
    try:
        ser=serial.Serial(serial_port,baud_rate,timeout=2)
        print(f"串口{serial_port}已打开，等待数据")
        while True:
            line_bytes=ser.readline()
            if not line_bytes:
                print("等待超时，未收到数据，正在重试")
                continue
            raw_data_from_fpga=line_bytes.decode('utf-8').strip()
            print(f"成功接收到原始fpga数据：{raw_data_from_fpga}")
            return raw_data_from_fpga
    except serial.SerialException as e:
        print(f"[错误!] 无法打开或读取串口 '{serial_port}'。")
        print(f"请检查: 1. FPGA是否已连接电脑。 2. 串口号是否正确。 3. 是否有其他程序占用了该串口。")
        print(f"详细错误信息: {e}")
        return None
    except Exception as e:
        print(f"未知错误{e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()
            print(f"串口{serial_port}已关闭")



def clean_data(raw_data:str):
    print("步骤2：正在清洗fpga数据")
    if not raw_data or not isinstance(raw_data,str):
        print("传入的原始数据无效")
        return None
    try:
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        processed_data={'timestamp':timestamp}
        parts=raw_data.split(',')
        for part in parts:
            key,value=part.split(':')
            key=key.strip()
            if key=='temp':
                processed_data['temperature']=float(value)
            elif key =='humi':
                processed_data['humidity']=float(value)
        if 'temperature' in processed_data and 'humidity' in processed_data:
            print(f"FPGA数据处理完成：{processed_data}")
            return processed_data
        else:
            print("原始数据格式不正确，未能解析出温度和湿度")
            return None
    except(ValueError,IndexError) as e:
        print(f"[错误] 解析数据时失败，请检查FPGA发送的数据格式是否为 'key:value,key:value'。")
        print(f"原始数据: '{raw_data}', 错误信息: {e}")
        return None

def visual_data(combined_data:dict):
    print("步骤四：正在进行数据可视化")
    try:
        fpga_temp=combined_data['temperature']
        fpga_humi=combined_data['humidity']
        weather_temp_str=combined_data['温度']
        weather_humi_str=combined_data['相对湿度']
        weather_temp=float(weather_temp_str.replace('℃',''))
        weather_humi=float(weather_humi_str.replace('%','').strip())
        timestamp=combined_data['timestamp']
        weather_condition=combined_data['天气']
    except (KeyError,ValueError) as e:
        print(f"[错误] 可视化失败，合并数据中缺少关键信息或格式不正确: {e}")
        return
    labels=['温度(℃)','湿度(%)']
    fpga_values=[fpga_temp,fpga_humi]
    weather_values=[weather_temp,weather_humi]
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
    plt.rcParams['axes.unicode_minus'] = False 
    x = np.arange(len(labels)) 
    width = 0.35  
    fig, ax = plt.subplots(figsize=(10, 7))
    rects1=ax.bar(x-width/2,fpga_values,width,label='室内(FPGA)',color='skyblue')
    rects2=ax.bar(x+width/2,weather_values,width,label='室内(天气)',color='sandybrown')
    ax.set_ylabel('数值')
    ax.set_title(f'室内外环境实时对比\n(时间：{timestamp}) | 天气：{weather_condition}')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    #ax.bar_label(rects1,padding=3)
    #ax.bar_label(rects2,padding=3)
    # 【兼容旧版的修改】手动遍历每个柱子，并在其顶部添加文本
    for rect in rects1:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.0, height, f'{height:.1f}', ha='center', va='bottom')

    for rect in rects2:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.0, height, f'{height:.1f}', ha='center', va='bottom')
    fig.tight_layout()
    output_filename='室内外温度对比.png'
    plt.savefig(output_filename)
    print(f"图表已成功保存到文件：{output_filename}")
    plt.show

    


if __name__=="__main__":
    city_code='54511'
    filename='BJQXJ_weather_data.csv'
    raw_fpga_data=receive_fpga_data()
    if raw_fpga_data:
        processed_fpga_data=clean_data(raw_fpga_data)
        if processed_fpga_data:
            print("---爬虫任务开始---")
            html=fetch_weather(city_code)
            if html:
                weather_data=parse_weather(html)
                if weather_data:
                    print("数据解析成功",weather_data)
                    combined_data = {**processed_fpga_data, **weather_data}
                    print("数据合并成功:", combined_data)
                    save_to_csv([weather_data],filename)
                    visual_data(combined_data)
                else:
                    print("数据解析失败")
            else:
                print("网页获取失败")
    print("---任务结束---")
