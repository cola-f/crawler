import win32com.client
import datetime as dt

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
    appointment.Categories = category

    appointment.Save()

subject = '제목'
location = '회의실'
dt.timezone(dt.timedelta(hours=9))
startDate = dt.datetime(2024, 5, 18, 0, 0, 0)
endDate = dt.datetime(2024, 5, 18, 1, 0, 0)
isAllday = False
bodyStr = '내용'
category = '할일'

insertOutlook(subject, location, startDate, endDate, isAllday, bodyStr)
templine = ''
file = open("outlook.txt", "r")
year = 2024
month = 5
day = 18
hour = 0
minute = 0
while True:
    #startDate 한줄을 parsing 한다.
    startText = file.readlines()
    if not startText:
        break
    date_regex = re.compile(r'(202\d (0[1-9])|(1[0-2])([0-2]\d)|(3[0-1]) ([0-1]\d)|(2[0-3])([0-5]\d))|(([0-1\d)|(2[0-3])([0-5]\d))')
    # 형식에 맞지 않는 시간이 있을 때는 다음 변수에 값을 넘겨준다
    if date_regex.findall(startText) == 0:
        templine = startText
        startText = input()
    else:
        templine = ''
    while date_regex.findall(startText) == 0:
        startText = input()
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
    if templine == '':
        subject = file.readlines()
    else:
        subject = templine
    if not subject:
        break
    location = file.readlines()
    if not location:
        break
    endText = file.readlines()
    if not endText:
        break
    if date_regex.findall(endText) == 0:
        templine = endText
        endText = input()
    else:
        templine = ''
    while date_regex.findall(endText) == 0:
        endText = input()
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
    line = readlines()
    if line =='':
        insertionOutlook(subject, location, startDate, endDate, isAllday, bodyStr, '')
        continue
    else:
        bodyStr = line
    while (line := readlines())!='':
        bodyStr += '\n' + line
    isAllday = False
    insertOutlook(subject, location, startDate, endDate, isAllday, bodyStr, '')
file.close()
