import RPi.GPIO as GPIO
from time import sleep
import datetime
from tkinter import *
import tkinter
from tkinter import ttk
from tkinter import font
from tkinter import filedialog
import firebase_admin
from firebase_admin import credentials, db, storage, auth
import threading
import serial
from uuid import uuid4
import os
from PIL import Image, ImageTk
import requests
#from io import BytesIO
import io
import base64
import copy
new_width = 40
new_height = int((3 * new_width) / 2)
port='/dev/ttyUSB0'
arduino = serial.Serial(port, 9600)
#from PIL import ImageTk, Image
locationGroup = dict()
userList = dict()
root = tkinter.Tk()
root.title("전자 인원 현황판")
root.minsize(1000,500)
root.resizable(0,0)
locationFrame = Frame(root)

cred = credentials.Certificate("personnelstatusplate-firebase-adminsdk-ggqlo-35d50549fa.json")
firebase_app = firebase_admin.initialize_app(cred, {
    'databaseURL': databaseURL,
    'storageBucket': storageURL
})
bucket = storage.bucket(app=firebase_app)

# user = auth.create_user(uid=str(uuid4()))
# token = auth.create_custom_token(user.uid)
# authed_user = auth.verify_id_token(token)

ref = db.reference('/users/')
ref_location = db.reference('/locationGroup/')
ref_reservation = db.reference('/reservation/')
ref_cardKey = db.reference('/cardKey/')
refRFID = db.reference('/readRFID')
class location:
    label_frame = LabelFrame()
    locationFrame
    def __init__(self, locationFrame, title):
        col = len(locationGroup)
        #self.label_frame = LabelFrame(locationFrame, text=title, padx=20, pady=20)
        #self.locationFrame = locationFrame
        #self.label_frame.pack(side="left", padx=10, pady=10)
        self.label_frame = LabelFrame(locationFrame, text = title, width=200, height=200, padx=50)
        self.locationFrame = locationFrame
        self.label_frame.grid(sticky="nsew", row=0, column=col)
        self.label_frame.columnconfigure(0, weight=1)
        #self.label_frame.pack(side="left", padx=5, pady=5)

    def refreshFrame(self):
        self.label_frame.update()
        self.label_frame.update_idletasks()

    def __del__(self):
        print("del")
        self.label_frame.pack_forget()

class user:
    pos = ""
    userFrame = LabelFrame()
    label = Label()

    userName = ""

    userImage = tkinter.PhotoImage(file="userImage.png")
    userQRImage = None

    def __init__(self, pos, userName, qr, userImageData):
        if(userImageData == "None"):
            self.userImage = tkinter.PhotoImage(file="userImage.png")
        else:
            try:
                print("들어오긴 하냐?")
                decoded_image = base64.b64decode(userImageData)
                self.userImage = PhotoImage(data=decoded_image)
                # 이미지를 화면에 출력하는 코드
            except Exception as e:
                print(f"Error decoding or opening image: {e}")
                print("Error")
                self.userImage = tkinter.PhotoImage(file="userImage.png")
                # 에러 처리 코드 추가


        self.userName = userName
        self.userQRImage = tkinter.PhotoImage(file="")
        self.userFrame = LabelFrame(locationGroup[pos].label_frame, text = userName)
        self.pos = pos

        self.label = tkinter.Label(self.userFrame, image=self.userImage)
        self.label.image = self.userImage
        self.label.bind("<Button-1>", self.userClick)
        self.label.pack(side='left', fill="none", expand=False, padx=5, pady=5)
        # self.label = tkinter.Label(self.userFrame, image=self.userImage)
        # self.label.image = self.userImage
        # self.label.bind("<Button-1>", self.userClick)
        # self.label.pack(fill="both", expand=True, padx=5, pady=5)
        self.userFrame.pack()

    def __del__(self):
        print("delll")
        self.userFrame.pack_forget()
        #self.label.pack_forget()
        #self.userFrame.pack_forget()
        #self.userInfo.destroy()


    def cleanup(self):
        print(f"{self.userName} 사용자에 대한 리소스 정리 중")
        self.userFrame.pack_forget()

    def refreshFrame(self):
        self.label.update()
        self.label.update_idletasks()
        self.userFrame.update()
        self.userFrame.update_idletasks()

    def userClick(self, e):
        userInfo = Toplevel()
        userInfo.title(self.userName + "님의 정보")
        userInfo.minsize(300, 300)
        userInfo.resizable(0,0)
        userQrImageView = tkinter.Label()
        def userQrImageUploadFunc():
            print("userQrImageUploadFunc")
            print(self.userName)

            userInfo.filename = filedialog.askopenfilename(initialdir='./png', title='파일선택', filetypes=(('png files', '*.png'), ))

            if userInfo.filename:
                # 파일을 Firebase Storage에 업로드합니다.
                encoded_image = encode_image_to_base64(userInfo.filename)
                user_edit = ref.get()
                user_edit[self.userName]['qr'] = encoded_image
                ref.set(user_edit)
                userInfo.destroy()

        def userImageUploadFunc():
            userInfo.filename = filedialog.askopenfilename(initialdir='./png', title='파일선택', filetypes=(('png files', '*.png'),))

            if userInfo.filename:
                # 파일을 Firebase Storage에 업로드합니다.
                img = Image.open(userInfo.filename)
                resized_img = img.resize((new_width, new_height), Image.ANTIALIAS)
                resized_img = resized_img.convert("RGB")  # 이미지가 RGBA(투명도 포함) 형식일 경우를 대비해 RGB로 변환
                resized_img.save(userInfo.filename, quality=5)  # 퀄리티 30으로 저장
                encoded_image = encode_image_to_base64(userInfo.filename)
                user_edit = ref.get()
                user_edit[self.userName]['userImage'] = encoded_image
                ref.set(user_edit)
                userImageRefresh(user_edit[self.userName])
                userInfo.destroy()

        def userCardKey():
            userCardInfo = Toplevel()
            userCardInfo.title(self.userName + "님의 카드키 등록")
            userCardInfo.minsize(300, 300)
            userCardInfo.resizable(0,0)

            refRFID.set("0")
            a=arduino.readline()
            a = a.decode()
            a = a[:12]
            card = ref_cardKey.get()
            if card == None:
                card = dict()
            refRFID.set("1")

            userCardKeyLabel = tkinter.Label(userCardInfo, text = ("인식된 카드 값 : " + a ))
            userCardKeyLabel.pack(fill="both", expand=True, padx=5, pady=5)

            if a in card:
                userCardKeyAlreadyLabel = tkinter.Label(userCardInfo, text = ("해당 카드가 등록된 유저 : " + card[a] ))
                userCardKeyAlreadyLabel.pack(fill="both", expand=True, padx=5, pady=5)

            userScheduleMake_btn = Button(userCardInfo, text="등록", command=lambda: userCardKeyRegist(card, a, self.userName, userCardInfo))
            userScheduleMake_btn.pack(side=LEFT, padx=10, pady=10)
            userScheduleCancel_btn = Button(userCardInfo, text="취소", command=userCardInfo.destroy)
            userScheduleCancel_btn.pack(side=LEFT, padx=10, pady=10)

        def userCardKeyRegist(cards, number, userName, userCardInfo):
            cards[number] = userName
            ref_cardKey.set(cards)
            print("등록 완")
            userCardInfo.destroy()

        def userMakeSchedule():
            userInfo = tkinter.Toplevel()
            userInfo.title(f"{self.userName}님의 일정 생성")
            userInfo.minsize(400, 300)
            userInfo.resizable(0, 0)

            style = ttk.Style()
            style.configure("TSpinbox", padding=(10, 5, 10, 5))  # Adjust the padding as needed
            style.configure("TCombobox", padding=(5, 2, 0, 2), width=5)  # Adjust padding and width as needed
            locationData = ref_location.get()
            options = list(locationData.keys())
            hour = [f"{i:02d}" for i in range(24)]
            minute = [f"{i:02d}" for i in range(0, 56, 5)]

            selected_Start_option = tkinter.StringVar()
            selected_End_option = tkinter.StringVar()
            selected_Start_hour = tkinter.StringVar()
            selected_Start_minute = tkinter.StringVar()
            selected_End_hour = tkinter.StringVar()
            selected_End_minute = tkinter.StringVar()

            start_hour_label = ttk.Label(userInfo, text="일정 시작 시간 (시):")
            start_hour_label.grid(row=0, column=0, padx=10, pady=10)
            start_hour = ttk.Combobox(userInfo, textvariable=selected_Start_hour, values=hour)
            start_hour.grid(row=0, column=1, padx=5, pady=10)
            start_hour.bind("<<ComboboxSelected>>")
            # start_hour_var = tkinter.StringVar(value="00")
            # start_hour_spinbox = ttk.Spinbox(userInfo, from_=0, to=23, textvariable=start_hour_var, wrap=True, width=2)
            # start_hour_spinbox.grid(row=0, column=1, padx=5, pady=10)

            start_minute_label = ttk.Label(userInfo, text="일정 시작 시간 (분):")
            start_minute_label.grid(row=0, column=2, padx=10, pady=10)
            start_minute = ttk.Combobox(userInfo, textvariable=selected_Start_minute, values=minute)
            start_minute.grid(row=0, column=3, padx=5, pady=10)
            start_minute.bind("<<ComboboxSelected>>")
            # start_minute_var = tkinter.StringVar(value="00")
            # start_minute_spinbox = ttk.Spinbox(userInfo, from_=0, to=55, increment=5, textvariable=start_minute_var, wrap=True, width=2)
            # start_minute_spinbox.grid(row=0, column=3, padx=5, pady=10)

            userScheduleStartMoveInfo = Button(userInfo, text="이동할 장소", state=DISABLED)
            userScheduleStartMoveInfo.grid(row=1, column=0, padx=10, pady=10)
            # Combobox widget
            userScheduleStartMove = ttk.Combobox(userInfo, textvariable=selected_Start_option, values=options)
            userScheduleStartMove.grid(sticky="nsew", row=1, column=1,columnspan=4, padx=5, pady=10)
            userScheduleStartMove.bind("<<ComboboxSelected>>")
            # userScheduleStartMove = Entry(userInfo)
            # userScheduleStartMove.grid(row=1, column=1,columnspan=4, padx=5, pady=10)

            end_hour_label = ttk.Label(userInfo, text="일정 종료 시간 (시):")
            end_hour_label.grid(row=2, column=0, padx=10, pady=10)
            end_hour = ttk.Combobox(userInfo, textvariable=selected_End_hour, values=hour)
            end_hour.grid(row=2, column=1, padx=5, pady=10)
            end_hour.bind("<<ComboboxSelected>>")
            # end_hour_var = tkinter.StringVar(value="00")
            # end_hour_spinbox = ttk.Spinbox(userInfo, from_=0, to=23, textvariable=end_hour_var, wrap=True, width=2)
            # end_hour_spinbox.grid(row=2, column=1, padx=5, pady=10)

            end_minute_label = ttk.Label(userInfo, text="일정 종료 시간 (분):")
            end_minute_label.grid(row=2, column=2, padx=10, pady=10)
            end_minute = ttk.Combobox(userInfo, textvariable=selected_End_minute, values=minute)
            end_minute.grid(row=2, column=3, padx=5, pady=10)
            end_minute.bind("<<ComboboxSelected>>")
            # end_minute_var = tkinter.StringVar(value="00")
            # end_minute_spinbox = ttk.Spinbox(userInfo, from_=0, to=55, increment=5, textvariable=end_minute_var, wrap=True, width=2)
            # end_minute_spinbox.grid(row=2, column=3, padx=5, pady=10)


            userScheduleEndMoveInfo = Button(userInfo, text="복귀할 장소", state=DISABLED)
            userScheduleEndMoveInfo.grid(row=3, column=0, padx=10, pady=10)
            userScheduleEndMove = ttk.Combobox(userInfo, textvariable=selected_End_option, values=options)
            userScheduleEndMove.grid(sticky="nsew", row=3, column=1, columnspan=3, padx=5, pady=10)
            userScheduleEndMove.bind("<<ComboboxSelected>>")
            # userScheduleEndMove = Entry(userInfo)
            # userScheduleEndMove.grid(row=3, column=1, columnspan=3, padx=5, pady=10)

            userScheduleMake_btn = tkinter.Button(userInfo, text="생성", command=lambda: userMakeScheduleClick(
                userInfo,
                start_hour.get(), start_minute.get(),
                end_hour.get(), end_minute.get(),
                self.userName,
                userScheduleStartMove.get(),
                userScheduleEndMove.get()
            ))
            userScheduleMake_btn.grid(row=4, column=0, columnspan=2, pady=10)

            userScheduleCancel_btn = tkinter.Button(userInfo, text="취소", command=userInfo.destroy)
            userScheduleCancel_btn.grid(row=4, column=2, columnspan=2, pady=10)


        def userMakeScheduleClick(userInfo, start_hour, start_minute, end_hour, end_minute, userName, startPos, endPos):
            Schedules = ref_reservation.get()
            if Schedules == None:
                Schedules = dict()
            start = start_hour+":"+start_minute
            end = end_hour+":"+end_minute
            Schedules[start] = {
                'name': userName,
                'pos': startPos,
                'time': start
            }
            Schedules[end] = {
                'name': userName,
                'pos': endPos,
                'time': end
            }

            ref_reservation.set(Schedules)
            userInfo.destroy()

        userImaegView = tkinter.Label(userInfo, image=self.userImage)
        userImaegView.image = self.userImage
        userImaegView.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        userNameLabel = tkinter.Label(userInfo, text = (self.userName + "님의 현재 위치 : " + self.pos))
        userNameLabel.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        userImageChange = tkinter.Button(userInfo, text = "프로필 사진 교체", command=userImageUploadFunc)
        userImageChange.grid(row=2, column=0, padx=5, pady = 5, sticky='NSEW')
        userCardKey = tkinter.Button(userInfo, text = "카드키 등록", command=userCardKey)
        userCardKey.grid(row=2, column=1, padx=5, pady = 5, sticky='NSEW')

        userReservation = tkinter.Button(userInfo, text = "일정 생성", command=userMakeSchedule)
        userReservation.grid(row=3, column=0,  padx=5, pady = 5, sticky='NSEW')

        userQrImageUpload = tkinter.Button(userInfo, text = "연락처 QR 변경", command=userQrImageUploadFunc)
        userQrImageUpload.grid(row=3, column=1, padx=5, pady = 5, sticky='NSEW')


        userData = ref.get()
        if userData[self.userName]['qr'] != "None":
            decoded_image = base64.b64decode(userData[self.userName]['qr'])
            pil_image = Image.open(io.BytesIO(decoded_image))
            resized_image = pil_image.resize((300, 300), Image.ANTIALIAS)
            tk_image = ImageTk.PhotoImage(resized_image)
            #tk_image = PhotoImage(data=decoded_image)
            userQrImageView = Label(userInfo, image=tk_image)
            userQrImageView.image = tk_image
            userQrImageView.grid(row=4, column=0, rowspan=2, columnspan=2, padx=5, pady=5)


            # try:
            #     print("들어옴")
            #     response = requests.get(userData[self.userName]['qr'])
            #     img_data = response.content
            #     img = Image.open(BytesIO(img_data))
            #     tk_img = ImageTk.PhotoImage(img)

            #     userQrImageView = Label(self.userInfo, image=tk_img)
            #     userQrImageView.image = tk_img
            #     userQrImageView.pack(fill="both", expand=True, padx=5, pady=5)
            # except Exception as e:
            #     print(f"이미지를 열 수 없습니다: {e}")
        userInfo.mainloop()

def on_close():
    event_stream.close()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image

def handle_event(event):
    data = ref.get()
    if(data == None) == False:
        for userName in data:
            print(data[userName]['pos'], userList[userName].pos, sep='|')
            if data[userName]['pos'] != userList[userName].pos:
                print("위치 변동 감지")
                MoveToLocationFunc(data[userName]['name'], data[userName]['pos'], data[userName]['qr'], data[userName]['userImage'])
    else:
        print("data None")


def periodicCheck(sec):
    while True:
        now = datetime.datetime.now()
        currentH = now.hour
        currentM = now.minute
        print(currentH,"시 ", currentM, "분 ",sep='')
        reservations = ref_reservation.get()
        userData = ref.get()

        if reservations != None:
            sorted(reservations.keys())
            for timer in reservations:
                h, m = reservations[timer]['time'].split(":")
                h = int(h)
                m = int(m)

                if h <= currentH and m <= currentM:
                    MoveToLocationFunc(reservations[timer]['name'], reservations[timer]['pos'], userData[reservations[timer]['name']]['qr'], userData[reservations[timer]['name']]['userImage'])
                    databaseTimer("del", timer)
                    print(timer)

        sleep(sec)

def dataRefresh(sec):
        data = ref.get()
        if(data == None) == False:
            for userName in data:
                print(data[userName]['pos'], userList[userName].pos, sep='|')
                if data[userName]['pos'] != userList[userName].pos:
                    print("위치 변동 감지")
                    MoveToLocationFunc(data[userName]['name'], data[userName]['pos'])
        else:
            print("data None")
        sleep(sec)

def EditTextRefresh():
    title = addGroupTitle.get()
    addGroupTitle.delete(0, len(addGroupTitle.get()))
    userMoveName.delete(0, len(userMoveName.get()))
    userMovePos.delete(0, len(userMovePos.get()))

    return title

def addButton():
    title = EditTextRefresh()
    location1 = location(locationFrame, title)
    #location1.label_frame.grid(row=0, column=len(locationGroup), padx=10, pady=10)
    locationGroup[title] = location1
    databaseLocation("add", title)

def deleteButton():
    title = EditTextRefresh()
    if(title == "Default"):
        print("Default는 삭제할 수 없습니다.")
    else:
        del locationGroup[title]
        databaseLocation("del", title)

def databaseLocation(way, location):
    locations = ref_location.get()
    if locations == None:
        locations = dict()

    if(way == "add"):
        locations[location] = {
            'name': location
        }

    elif(way == "del"):
        if location in locations:
            del locations[location]

    ref_location.set(locations)

def databaseTimer(way, time):
    timer = ref_reservation.get()
    if timer == None:
        timer = dict()

    if(way == "add"):
        timer[time] = {
            'time': location
        }

    elif(way == "del"):
        if time in timer:
            del timer[time]

    ref_reservation.set(timer)

def refreshButton():
    for key in locationGroup.keys():
        locationGroup[key].refreshFrame()
    EditTextRefresh()

def addUserButton():
    userName = userMoveName.get()
    posName = userMovePos.get()
    if (userName in userList) == False:
        if(posName == ""):
            posName = "Default"
        userList[userName] = user(posName, userName, "None", "None")
        databaseRefresh("add", userList[userName].userName, userList[userName].pos) # 사용자 추가
    else:
        print("중복된 이름")
    EditTextRefresh()

def delUserButton():
    userName = userMoveName.get()
    if userName in userList:
        databaseRefresh("del", userList[userName].userName, userMovePos.get()) # 사용자 삭제
        userList[userName].cleanup()  # 정리 메서드 호출
        del userList[userName]
    EditTextRefresh()

def MoveToLocation():
    userName = userMoveName.get()
    if userName in userList:
        qr = copy.deepcopy(userList[userName]['qr'])
        userImage = copy.deepcopy(userList[userName]['userImage'])
        userList[userName].cleanup()  # 정리 메서드 호출
        del userList[userName]
        userList[userName] = user(userMovePos.get(), userName, qr, userImage)
        databaseRefresh("move", userList[userName].userName, userMovePos.get()) # 사용자 장소 변경
        EditTextRefresh()

def MoveToLocationFunc(name, pos, qr, userImage):
    # userList = ref.get()
    # if(userList == None):
    #     userList = dict()
    if (qr == None):
        qr = "None"
    if(userImage == None):
        userImage = "None"
    if name in userList:
        userList[name].cleanup()  # 정리 메서드 호출
        del userList[name]
        userList[name] = user(pos, name, qr, userImage)
        databaseRefresh("move", userList[name].userName, pos) # 사용자 장소 변경

def userImageRefresh(userData):
        name = userData['name']
        pos = userData['pos']
        qr = userData['qr']
        userImage = userData['userImage']
        userList[name].cleanup()  # 정리 메서드 호출
        del userList[name]
        userList[name] = user(pos, name, qr, userImage)

def refreshUserFrame():
    for key in userList.keys():
        userList[key].refreshFrame()
    EditTextRefresh()

def databaseRefresh(way, userName, pos):
    data = ref.get()
    if(way == "add"):
        if(data == None):
            data = dict()
        data[userName] = {
            'name': userName,
            'pos': pos,
            'qr': "None",
            'userImage': "None"
        }

    elif(way == "move"):
        if userName in data:
            data[userName]['pos'] = pos

    elif(way == "del"):
        if userName in data:
            del data[userName]

    ref.set(data)

def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    root.geometry(f"{width}x{height}+{x}+{y}")

def show_setting_frame():
    settingInfo.deiconify()  # 프레임을 보이게 설정

def hide_setting_frame():
    settingInfo.withdraw()  # 프레임을 숨기게 설정
# root.grid_rowconfigure(0, weight=1)
# root.grid_columnconfigure(1, weight=1)

# # 데이터베이스의 참조 가져오기
# refDB = db.reference()  # 실제 데이터베이스 경로로 변경

button_width = 35
button_height = 35

settingFrame = Frame(root)
settingFrame.pack(side=TOP, padx=70, pady=10, fill=tkinter.X)
icon_Setting = tkinter.PhotoImage(file="icon_setting.png")
icon_Setting = icon_Setting.subsample(int(icon_Setting.width() / button_width), int(icon_Setting.height() / button_height))
setting_btn = Button(settingFrame, command=show_setting_frame, image=icon_Setting, width=button_width, height=button_height, borderwidth=0, highlightthickness=0)
setting_btn.grid(row=0, column=3, sticky=NE)
settingFrame.columnconfigure(3, weight=1)

settingInfo = Toplevel()
settingInfo.title("setting")
settingInfo.minsize(300, 300)
settingInfo.resizable(0,0)
settingInfo.withdraw()
settingInfo.protocol("WM_DELETE_WINDOW", hide_setting_frame)

# 그룹 추가 Frame
edtFrame = Frame(settingInfo)
edtFrame.pack()
addGroupTitle = Entry(edtFrame)
addGroupTitle.pack(side=LEFT, padx=10, pady=10)
addBtn = Button(edtFrame, text="ADD", command=addButton)
addBtn.pack(side=LEFT, padx=10, pady=10)
del_btn = Button(edtFrame, text="DEL", command=deleteButton)
del_btn.pack(side=LEFT, padx=10, pady=10)
refresh_btn = Button(edtFrame, text="Refresh", command=refreshButton)
refresh_btn.pack(side=LEFT, padx=10, pady=10)

# 유저 이동 Frame
userMoveFrame = Frame(settingInfo)
userMoveFrame.pack()
userMoveNameInfo = Button(userMoveFrame, text="User Name", state=DISABLED)
userMoveNameInfo.pack(side=LEFT, padx=10, pady=10)
userMoveName = Entry(userMoveFrame)
userMoveName.pack(side=LEFT, padx=10, pady=10)
userMovePosInfo = Button(userMoveFrame, text="Move Position Name", state=DISABLED)
userMovePosInfo.pack(side=LEFT, padx=10, pady=10)
userMovePos = Entry(userMoveFrame)
userMovePos.pack(side=LEFT, padx=10, pady=10)

userMove_btn = Button(userMoveFrame, text="MoveUser", command=MoveToLocation)
userMove_btn.pack(side=LEFT, padx=10, pady=10)
addUser_btn = Button(userMoveFrame, text="AddUser", command=addUserButton)
addUser_btn.pack(side=LEFT, padx=10, pady=10)
delUser_btn =  Button(userMoveFrame, text="DelUser", command=delUserButton)
delUser_btn.pack(side=LEFT, padx=10, pady=10)

locationFrame.pack()

locationData = ref_location.get()
if(locationData == None):
    addGroupTitle.insert(0, "Default")
    addButton()
else:
    for locations in locationData:
        addGroupTitle.insert(0, locationData[locations]['name'])
        addButton()

data = ref.get()
if(data == None) == False:
    for userName in data:
        userList[userName] = user(data[userName]['pos'], data[userName]['name'], data[userName]['qr'], data[userName]['userImage'])

event_stream = ref.listen(handle_event)


timmer = {
    "15:53": {
        'name': 'kan96j',
        'pos': 'Edu',
        'time': '15:53'
    },
    "15:54": {
        'name': 'kan96j',
        'pos': 'Default',
        'time': '15:54'
    }
}

# ref_reservation.set(timmer)

t1 = threading.Thread(target=periodicCheck, args=(60,))
#refreshThreading = threading.Thread(target=dataRefresh, args=(10,))
t1.daemon = True
#refreshThreading.daemon = True
t1.start()
#refreshThreading.start()

#userList[userName] = user('Default', userName)
#root.protocol("WM_DELETE_WINDOW", on_close)
center_window(root, 1000, 500)
root.mainloop()

