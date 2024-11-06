"""
扫描模块
"""
import os
import importlib.util
import json


def get_command_module_dict(modules_path='./module'):
    """
    扫描指定目录下的所有 .py 文件，动态导入每个文件中的 FunctionModule 类，
    并构建一个字典，以对应命令值为键，功能模块对象为值。

    同时，调用每个模块的 get_simple_description() 方法，
    将简单介绍以 JSON 格式保存在 data 文件夹下。

    参数：
        modules_path (str): 要扫描的目录路径。默认值为 '/module'。

    返回：
        dict: 包含 command_sign 和对应功能模块对象的字典。
    """
    # 用于存储不同模块命令对应的功能模块对象
    command_module_dict = {}
    # 用于存储模块的简单介绍
    description_dict = {}

    # 遍历指定目录下的所有文件
    for root, _, files in os.walk(modules_path):
        for file in files:
            if file.endswith('.py'):
                # 获取每个 .py 文件的完整路径
                py_file_path = os.path.join(root, file).replace("\\", "/")

                # 动态加载模块
                spec = importlib.util.spec_from_file_location("module.name", py_file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 获取 FunctionModule 类
                function_module = getattr(module, 'FunctionModule', None)
                if function_module is None or not function_module.is_active:
                    continue  # 如果模块中没有 FunctionModule 类，则跳过该文件
                print(file)
                # 实例化 FunctionModule 类
                function_module_instance = function_module()

                # 调用 get_command_sign 方法获取返回值
                command_sign = function_module_instance.get_command_sign()

                # 调用 get_simple_description 方法获取简单介绍
                description = function_module_instance.get_simple_description()

                # 根据返回值更新字典
                if isinstance(command_sign, list):
                    for sign in command_sign:
                        command_module_dict[sign] = function_module_instance
                    # 使用第一个命令作为键，保存简单介绍
                    if command_sign:
                        description_dict[command_sign[0]] = description
                else:
                    command_module_dict[command_sign] = function_module_instance
                    description_dict[command_sign] = description

    # 确保 data 文件夹存在
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 将描述信息保存为 JSON 格式
    description_file_path = os.path.join(data_dir, 'description.json')
    with open(description_file_path, 'w', encoding='utf-8') as f:
        json.dump(description_dict, f, ensure_ascii=False, indent=4)

    return command_module_dict
