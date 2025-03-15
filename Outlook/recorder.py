import win32com.client
import datetime as dt
import re
import tkinter

def insertOutlook(subject, location, startDate, endDate, isAllday, bodyStr, category):
    outlook = win32com.client.Dispatch('Outlook.Application')
    appointment = outlook.CreateItem(1)

    appointment.Subject = subject
    appointment.Location = location
    appointment.Start = startDate + dt.timedelta(hours=9)

    if not isAllday:
        appointment.End = endDate + dt.timedelta(hours=9)

    appointment.AllDayEvent = isAllday
    appointment.Body = bodyStr
    appointment.BusyStatus = 0

    appointment.Save()

#subject = '제목'
#location = '회의실'
#dt.timezone(dt.timedelta(hours=9))
#startDate = dt.datetime(2024, 5, 29, 0, 0, 0)
#endDate = dt.datetime(2024, 5, 29, 1, 0, 0)
#isAllday = False
#bodyStr = '내용'
#category = '할일'
#
#insertOutlook(subject, location, startDate, endDate, isAllday, bodyStr, '')

queue = []
file = open("outlook.txt", "r", encoding='UTF=8')
year = dt.datetime.today().year
month = dt.datetime.today().month
day = dt.datetime.today().day
hour = dt.datetime.today().hour
minute = dt.datetime.today().minute
error = ''
date_regex = re.compile(r'(^202\d (0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01]) (0[0-9]|1[0-9]|2[0-3])(0[1-9]|[0-5][0-9])$)|(^(0[0-9]|1[0-9]|2[0-3])(0[1-9]|[0-5][0-9])$)')
writable = False

def verification():
        def on_submit():
            nonlocal local_queue
            local_queue = text_widget.get("1.0", tkinter.END).split('\n')[:-1]
            root.destroy()
        root = tkinter.Tk()
        root.title("Input Text")

        text_widget = tkinter.Text(root, height=10, width=50)
        text_widget.pack()
        text_widget.insert(tkinter.CURRENT, queue.pop(0))
        for item in queue:
            text_widget.insert(tkinter.CURRENT, '\n' + item)

        submit_button = tkinter.Button(root, text="Submit", command=on_submit)
        submit_button.pack()

        input_text = ""
        local_queue = []
        root.mainloop()
        return local_queue

for text in file:
    queue.append(text.replace('\n', ''))
    if(len(queue)>4 and text.replace('\n', '') == ''):
        writable = True
    while writable == True:
        #검증과정
        error = '?'
        # error를 '?'로 두고 error==''가 될 때까지 검증한다.
        while error != '':
            if len(date_regex.findall(queue[0])) == 0:
                error = "startDate error"
                print("startDate error")
            elif len(date_regex.findall(queue[3])) == 0:
                error = "endDate error"
                print("endDate error")
            else:
                startText = queue[0]
                tempYear = year
                tempMonth = month
                tempDay = day
                if len(startText.split(' ')) > 2:
                    print("test0")
                    tempYear = int(startText.split(' ')[0])
                    tempMonth = int(startText.split(' ')[1][0:2])
                    print("test1")
                    tempDay = int(startText.split(' ')[1][2:4])
                    startDate = dt.datetime(tempYear, tempMonth, tempDay, int(startText.split(' ')[2][0:2]), int(startText.split(' ')[2][2:4]))
                else:
                    startDate = dt.datetime(tempYear, tempMonth, tempDay, int(startText[0:2]), int(startText[2:4]))
                endText = queue[3]
                if len(endText.split(' ')) > 2:
                    tempYear = int(endText.split(' ')[0])
                    tempMonth = int(endText.split(' ')[1][0:2])
                    tempDay = int(endText.split(' ')[1][2:4])
                    endDate = dt.datetime(tempYear, tempMonth, tempDay, int(endText.split(' ')[2][0:2]), int(endText.split(' ')[2][2:4]))
                else:
                    endDate = dt.datetime(tempYear, tempMonth, tempDay, int(endText[0:2]), int(endText[2:4]))
                if startDate > endDate:
                    error = "start>end error"
                    print("start>end error")
                else:
                    error = ""

            if error != '':
                queue = verification()
            print("error: ", error)

        startText = queue.pop(0)
        if len(startText.split(' ')) > 2:
            year = int(startText.split(' ')[0])
            month = int(startText.split(' ')[1][0:2])
            day = int(startText.split(' ')[1][2:4])
            hour = int(startText.split(' ')[2][0:2])
            minute = int(startText.split(' ')[2][2:4])
        else:
            hour = int(startText[0:2])
            minute = int(startText[2:4])
        startDate = dt.datetime(year, month, day, hour, minute)
        subject = queue.pop(0)
        location = queue.pop(0)
        endText = queue.pop(0)
        if len(endText.split(' ')) > 2:
            year = int(endText.split(' ')[0])
            month = int(endText.split(' ')[1][0:2])
            day = int(endText.split(' ')[1][2:4])
            hour = int(endText.split(' ')[2][0:2])
            minute = int(endText.split(' ')[2][2:4])
        else:
            hour = int(endText[0:2])
            minute = int(endText[2:4])
        endDate = dt.datetime(year, month, day, hour, minute)
        bodyStr = ''
        while (line := queue.pop(0))!='':
            bodyStr += line + '\n'
        bodyStr = bodyStr[:-1]
        isAllday = False
        print("================")
        print("startDate: ", startDate)
        print("subject: ", subject)
        print("location: ", location)
        print("endDate: ", endDate)
        print("bodyStr: ", bodyStr)
        #insertOutlook(subject, location, startDate, endDate, isAllday, bodyStr, '')
        if len(queue)<4:
            writable = False
            break

file.close()
