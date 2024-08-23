import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import zipfile, os, shutil
from tkinter import messagebox

root = tk.Tk()
root.geometry("420x460")
root.title("TagStudio Setup")
root.resizable(0, 0)

next_button = None

imgo = Image.open("media/header.png").resize((420, 160))
img = ImageTk.PhotoImage(imgo)
root.imgj = img

conframe = ttk.Frame(root)
conframe.place(x=0, y=160, width=420, height=300)

run=1
phase = 0
stated = "normal"  # Initialize state of the 'Next' button

def chphase():
    global phase, stated
    phase += 1
    rndrphase()
    stated = "normal"  # Reset state to normal when changing phase

def stop():
    global phase, stated,run
    phase = 5
    run=0
    rndrphase()
    stated = "normal"  # Reset state to normal when changing phase

def prphase():
    global phase, stated
    phase -= 1
    rndrphase()
    stated = "normal"  # Reset state to normal when changing phase

def toggle_next_button(*args):
    global phase, stated
    if phase == 1:
        print(agree_var.get())
        if not agree_var.get():
            stated = "disabled"
        else:
            stated = "normal"
    else:
        stated = "normal"
    if phase not in [2,3,4,5]:
        global next_button
        next_button = ttk.Button(conframe, text="Next", command=chphase, state=stated)
        next_button.place(x=330, y=260)

tagstudio_dval = tk.StringVar()
tagstudio_dval.set("C:/Program Files/TagStudio")
tagstudio_directory = "C:/Program Files/TagStudio"
input_box = None

tagstudio_progressbar, tagstudio_title = 0, "Creating directory"

def subinsttag():
    global tagstudio_directory, tagstudio_dval, phase
    tagstudio_directory = tagstudio_dval.get()
    print(tagstudio_directory)
    phase+=1
    rndrphase()
    t=threading.Thread(target=compile_pr)
    t.start()
    t=threading.Thread(target=compile)
    t.start()

def compile():
    global tagstudio_progressbar, tagstudio_title, phase, run, stated

    try:
        os.mkdir(tagstudio_directory)
        tagstudio_progressbar+=1
    except FileExistsError as e:
        tagstudio_progressbar+=1
    except:
        stop()
    
    tagstudio_title = "Preparing Installation"
    try:
        pyexe=zipfile.ZipFile("data/pyport.zip")
        appxe=zipfile.ZipFile("data/software.zip")
    except:
        stop()
    tagstudio_progressbar+=3

    tagstudio_title = "Downloading Python Portable"
    try:
        pyexe.extractall("tmp/py")
    except:
        stop()
    tagstudio_progressbar+=10

    tagstudio_title = "Downloading TagStudio Source"
    try:
        appxe.extractall("tmp/sw")
    except:
        stop()
    tagstudio_progressbar+=10

    tagstudio_title = "Installing Libraries"
    print(tagstudio_title)
    module="""humanfriendly==10.0
opencv_python>=4.8.0.74,<=4.9.0.80
Pillow==10.3.0
PySide6==6.7.1
PySide6_Addons==6.7.1
PySide6_Essentials==6.7.1
typing_extensions>=3.10.0.0,<=4.11.0
ujson>=5.8.0,<=5.9.0
numpy==1.26.4
rawpy==0.21.0
pillow-heif==0.16.0
chardet==5.2.0
ruff==0.4.2
pre-commit==3.7.0
pytest==8.2.0
Pyinstaller==6.6.0
mypy==1.10.0
syrupy==4.6.1"""
    with open("req.txt", "w") as f:
        f.write(module)
    
    os.system('"tmp\\py\\Scripts\\pip.exe" install -r req.txt')
    tagstudio_title = "Compiling TagStudio"
    tagstudio_progressbar+=25
    os.system('PyInstaller --name "TagStudio" --windowed --no-console --icon "tmp/sw/tagstudio/resources/icon.ico" --add-data "tmp/sw/tagstudio/resources:./resources" --add-data "tmp/sw/tagstudio/src:./src" -p "tmp/sw/tagstudio" --console --onefile "tmp/sw/tagstudio/tag_studio.py"')
    tagstudio_progressbar+=25

    tagstudio_title = "Deleting temp files"
    print(tagstudio_title)
    shutil.rmtree("tmp/sw")
    shutil.rmtree("tmp/py")
    shutil.rmtree("build")
    tagstudio_progressbar+=11

    tagstudio_title = "Moving build"
    print(tagstudio_title)
    
    try:
        with open(f"{tagstudio_directory}/TagStudio.exe", "w") as file:
            file.write("Executable not ready yet. ")
        shutil.copy("dist/TagStudio.exe", f"{tagstudio_directory}/TagStudio.exe")
        tagstudio_progressbar+=10
        
        tagstudio_title = "Finishing"
        print(tagstudio_title)
        tagstudio_progressbar+=5
        shutil.rmtree("dist")
    except:
        stop()
    
    chphase()
    stated = "normal"  # Reset state to normal when changing phase

def compile_pr():
    global tagstudio_progressbar, tagstudio_title, phase
    while (run):
        ttk.Label(conframe, text=tagstudio_title+" | Please do not close the app as\nthe Setup application will crash.").place(x=40, y=60)
        ttk.Progressbar(conframe, value=tagstudio_progressbar, maximum=100,length=350).place(x=40,y=180)
    print('End interrupt')

def exit():
    root.quit()

def rndrphase():
    global next_button, agree_var, stated, input_box

    # Clear the frame
    for widget in conframe.winfo_children():
        widget.destroy()
    
    ttk.Label(root, image=img).place(x=0, y=0)  # Header is placed here
    
    if phase == 0:
        ttk.Label(conframe, text="Welcome to TagStudio Setup!\n\nThis Setup will guide you through installing TagStudio. The free & open-source\ntag-based file manager. To start the installation, make sure that\nthe application is run as admin, and\nclick the 'Next' button").place(x=20, y=20)
    
    elif phase == 1:
        ttk.Label(conframe, text="Please read the license").place(x=20, y=10)

        # Create shadow effect with a background frame
        shadow_frame = tk.Frame(conframe, bg="gray", width=380, height=210)
        shadow_frame.place(x=19, y=39)

        # Scrollable Frame for License
        bg_frame = tk.Frame(conframe, bg="white", width=380, height=210)
        bg_frame.place(x=20, y=40)

        canvas = tk.Canvas(bg_frame, bg="white", width=360, height=190, bd=0, highlightthickness=0)
        scrollable_frame = ttk.Frame(canvas)
        scrollbar = ttk.Scrollbar(bg_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Attach scrollbar to the right of the canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_frame_configure)

        # Load license content from a file
        with open("GPL-3.0.txt", "r") as file:
            gpl_text = file.read()

        # Insert license text into scrollable frame
        for line in gpl_text.splitlines():
            ttk.Label(scrollable_frame, text=line, anchor="w", justify="left", wraplength=360).pack(anchor="w", pady=1)

        # Checkbox for agreement
        global agree_var
        agree_var = tk.BooleanVar()
        agree_check = ttk.Checkbutton(conframe, text="I agree to the license terms", variable=agree_var, command=toggle_next_button)
        agree_check.place(x=20, y=260)

        # Initial check to set the button state correctly
        agree_var.trace_add("write", toggle_next_button)
        toggle_next_button()  # Update button state based on the current phase
    
    elif phase == 2:
        ttk.Label(conframe, text="Where do you want to install TagStudio?").place(x=20, y=10)
        input_box = ttk.Entry(conframe, textvariable=tagstudio_dval, width=30)
        input_box.place(x=40,y=40)
        
        ttk.Button(conframe, text="Next", command=subinsttag, state=stated).place(x=330, y=260)

    elif phase == 3:
        ttk.Label(conframe, text="Compiling TagStudio", font=("Arial", 20, "bold")).place(x=20, y=20)
        ttk.Button(conframe, text="Cancel", command=stop, state=stated).place(x=330, y=260)
    
    elif phase == 4:
        ttk.Label(conframe, text="You have finished installing TagStudio, Press Finish to exit\nthe setup.").place(x=20, y=10)
        ttk.Button(conframe, text="Finish", command=exit).place(x=330, y=260)
    
    elif phase == 5:
        ttk.Label(conframe, text="The setup was interrupted by the user.").place(x=20, y=10)
        ttk.Button(conframe, text="Finish", command=exit).place(x=330, y=260)


    # Always create the 'Next' button and 'Back' button
    if not phase in [0,3,4,5]: 
        ttk.Button(conframe, text="Back", command=prphase).place(x=230, y=260)
    
    render=not phase in [2,3,4,5]
    print(render, "re", phase)
    if render:
        ttk.Button(conframe, text="Next", command=chphase, state=stated).place(x=330, y=260)
    # Update the state of the 'Next' button
    toggle_next_button()

rndrphase()  # Start at phase 0

root.mainloop()
run=0