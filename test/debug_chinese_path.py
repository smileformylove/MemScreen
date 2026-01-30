#!/usr/bin/env python3
"""
中文路径诊断工具

用于诊断 MemScreen 中文路径显示问题
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_path_operations():
    """测试基本的路径操作"""
    print("=" * 60)
    print("1. 基础路径操作测试")
    print("=" * 60)

    # 测试中文路径
    test_path = "~/桌面/测试目录/测试文件.txt"
    expanded_path = os.path.expanduser(test_path)

    print(f"原始路径: {test_path}")
    print(f"展开路径: {expanded_path}")
    print(f"路径存在: {os.path.exists(expanded_path)}")
    print(f"路径类型: {type(expanded_path)}")
    print(f"路径编码: {expanded_path.encode('utf-8')}")
    print()

def test_file_loader():
    """测试 FileLoader"""
    print("=" * 60)
    print("2. FileLoader 测试")
    print("=" * 60)

    from memscreen.file_loader import FileLoader

    test_path = "~/桌面/测试目录/测试文件.txt"
    expanded_path = os.path.expanduser(test_path)

    if not os.path.exists(expanded_path):
        print(f"⚠️  测试文件不存在: {expanded_path}")
        print("请先创建测试文件:")
        print(f"  mkdir -p ~/桌面/测试目录")
        print(f"  echo '简体中文测试' > ~/桌面/测试目录/测试文件.txt")
        return

    try:
        # 读取文件
        content = FileLoader.read_file_clean(expanded_path)
        filename = FileLoader.get_filename(expanded_path)

        print(f"✅ 文件读取成功")
        print(f"   文件名: {filename}")
        print(f"   内容长度: {len(content)} 字符")
        print(f"   内容预览: {content[:50]}...")
        print()

    except Exception as e:
        print(f"❌ 文件读取失败: {e}")
        import traceback
        traceback.print_exc()
        print()

def test_kivy_filechooser():
    """测试 Kivy FileChooser"""
    print("=" * 60)
    print("3. Kivy FileChooser 测试")
    print("=" * 60)

    try:
        from kivy.uix.filechooser import FileChooserListView
        from kivy.base import runTouchApp
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup
        import os

        print("启动 Kivy FileChooser 测试窗口...")
        print("请在打开的窗口中选择中文文件名")
        print()

        class TestApp:
            def __init__(self):
                self.layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

                # 按钮
                btn = Button(
                    text='打开文件选择器',
                    font_size=20,
                    size_hint_y=None,
                    height=50
                )
                btn.bind(on_press=self.show_filechooser)
                self.layout.add_widget(btn)

                # 状态标签
                self.status_label = Label(
                    text='等待选择文件...',
                    font_size=16,
                    size_hint_y=None,
                    height=100
                )
                self.layout.add_widget(self.status_label)

            def show_filechooser(self, instance):
                """显示文件选择器"""
                print("\n[FileChooser] 打开文件选择器")

                # 创建文件选择器
                filechooser = FileChooserListView(
                    path=os.path.expanduser('~'),
                    size_hint=(0.9, 0.75)
                )

                # 监听选择事件
                def on_selection(fc, selection):
                    if selection:
                        selected = selection[0]
                        print(f"[FileChooser] 选择: {selected}")
                        print(f"[FileChooser]   类型: {type(selected)}")
                        print(f"[FileChooser]   编码: {selected.encode('utf-8')}")

                        # 更新状态
                        self.status_label.text = f"已选择:\n{selected}\n\n检查控制台输出"

                filechooser.bind(selection=on_selection)

                # 确认按钮
                confirm_btn = Button(
                    text='关闭',
                    font_size=16,
                    size_hint_y=None,
                    height=50
                )

                # 布局
                popup_layout = BoxLayout(orientation='vertical', spacing=10)
                popup_layout.add_widget(filechooser)
                popup_layout.add_widget(confirm_btn)

                # 弹窗
                popup = Popup(
                    title='选择文件（测试中文显示）',
                    content=popup_layout,
                    size_hint=(0.9, 0.8)
                )

                confirm_btn.bind(on_press=lambda btn: popup.dismiss())
                popup.open()

        from kivy.app import App
        from kivy.uix.label import Label

        class DiagnosticApp(App):
            def build(self):
                app = TestApp()
                return app.layout

        print("启动 Kivy 测试应用...")
        print("请测试以下内容：")
        print("1. 文件对话框中的中文文件名是否正确显示")
        print("2. 选择中文文件后控制台输出的路径是否正确")
        print()

        # 不自动运行，只是提示
        print("⚠️  需要手动测试 Kivy FileChooser")
        print("   请在主应用中测试文件选择功能")
        print()

    except ImportError as e:
        print(f"❌ Kivy 未安装: {e}")
        print()

def test_system_encoding():
    """测试系统编码"""
    print("=" * 60)
    print("4. 系统编码信息")
    print("=" * 60)

    import sys
    import locale

    print(f"Python 版本: {sys.version}")
    print(f"默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print(f"本地设置: {locale.getpreferredencoding()}")
    print(f"环境变量 LANG: {os.environ.get('LANG', '未设置')}")
    print()

def main():
    print("\n" + "=" * 60)
    print("  MemScreen 中文路径诊断工具")
    print("=" * 60)
    print()

    # 运行所有测试
    test_system_encoding()
    test_basic_path_operations()
    test_file_loader()
    test_kivy_filechooser()

    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 查看 Chat 界面文件选择对话框中中文是否正确显示")
    print("2. 选择中文文件后查看控制台输出")
    print("3. 查看 Chat 界面中加载的文件内容是否正确")
    print()

if __name__ == '__main__':
    main()
