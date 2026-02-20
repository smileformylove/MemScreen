# macOS Kivy  - 

## 

- ✅ Kivy v2.3.1
- ✅ OpenGL  SDL2 
- ✅ 
- ❌ 
- ❌  Dock 

## 

** macOS **

### 

1. ✅ Kivy 
2. ✅ SDL2 
3. ✅ OpenGL 
4. ✅ Terminal  Accessibility 
5. ❌ SDL2  macOS 

## 

### 1. macOS  SDL2 

macOS  SDL2 

****
-  Terminal/Python "Screen Recording" 
-  Terminal/Python "Full Disk Access" 
-  Terminal

### 2. Python 

 Python 

****
```bash
#  Python
/usr/bin/python3 -m pip install kivy[base]
/usr/bin/python3 your_script.py
```

### 3. SDL2 

 SDL2 

****
```bash
#  SDL2 
otool -L /opt/homebrew/lib/libSDL2-2.0.0.dylib 2>/dev/null | head -5

# 
find /usr/local -name "*SDL2*" 2>/dev/null
```

### 4. Python 3.13 

Python 3.13 Kivy 

****
```bash
#  Python 3.11  3.12
brew install python@3.11
/usr/bin/python3.11 -m pip install kivy[base]
```

## 

###  1

1.  ****
2.  ****
3.  ****
4. 
   - **** "Terminal"  "Python"
   - **** "Terminal"  "Python"
   - **** "Terminal"  "Python"

###  2 Terminal

```bash
#  Terminal
#  Terminal
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
```

###  3 Kivy

```bash
source venv/bin/activate
python3 -c "
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Test Window')
    def on_start(self):
        print('Window should be visible')

TestApp().run()
"
```

###  4 Kivy

```bash
#  Kivy
deactivate
rm -rf venv

# 
python3 -m venv venv
source venv/bin/activate

#  Kivy 
pip install 'kivy[base]<2.3.0'
pip install -r requirements.txt
```

## 



###  A Tkinter

```python
import tkinter as tk

root = tk.Tk()
root.title("MemScreen")
root.geometry("1200x800")
label = tk.Label(root, text="MemScreen Running", font=("Arial", 24))
label.pack(expand=True)
root.mainloop()
```

###  B PyQt5

```bash
pip install PyQt5
```

###  C PySimpleGUI

```bash
pip install PySimpleGUI
```

## 

** Tkinter **

1. ✅ Tkinter  macOS 
2. ✅  SDL2
3. ✅  macOS 
4. ✅  SDL2 

### 



```bash
# 
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
/Users/jixiangluo/Documents/project_code/repository/MemScreen/venv/bin/python start.py

#  home 
~/memscreen.sh
```

## 



```bash
# 1. macOS 
sw_vers

# 2. Python 
python3 --version

# 3.  SDL2
find /opt/homebrew -name "*SDL2*" 2>/dev/null

# 4.  Tkinter 
python3 -c "import tkinter as tk; r=tk.Tk(); r.title('Test'); r.geometry('400x300'); tk.Label(r,text='Visible?').pack(); r.mainloop()"

# 5. 
tail -100 ~/.kivy/logs/kivy_26-02-05_*.txt
```

## 


- Email: jixiangluo85@gmail.com
- GitHub: https://github.com/smileformylove/MemScreen/issues
