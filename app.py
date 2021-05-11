import os
from flask import *
import sqlite3 as sql
from KMP import *
from Regex import *
from database import *
from datetime import *
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Create stemmer
factory = StemmerFactory()
stemmer = factory.create_stemmer()

app = Flask(__name__)

# List of commands
command = [
    'tambah', 'ingetin', 'ingat',                           # Menambah task baru (poin 1) 
    'update', 'ubah', 'undur', 'maju', 'baharu', 'baru',    # Update task (poin 4)
    'deadline', 'kumpul', 'tenggat', 'ngumpulin',           # Melihat deadline (poin 2 dan 3)
    'selesai', 'kelar', 'beres', 'rampung',                 # Selesai mengerjakan task (poin 5)
    'help', 'laku', 'perintah', 'bantu',                    # Menampilkan help (poin 6)
    'paansi'
]

# Global variable init
chat = []   # Array of chats, menyimpan data chat
nchat = 0   # length of Array of chat, untuk menentukan harus diletakkan di bubble kanan atau kiri

@app.route("/", methods = ['POST', 'GET'])
def index():
    connection = connect()      # Connecet ke database
    createTables(connection)    # Membuat database baru jika belum ada
    
    # Inisialisasi pesan awal bot
    if (len(chat) == 0):
        chat.append("Selamat datang di jam-bot (red: jamboard), masukkan perintah anda")
        
    # Request query dari home.html
    if (request.method == 'POST'):
        query = request.form['query']
        # Append query dari user ke array of chat
        chat.append(query)
        # Stemming query
        stemmedQuery = query
        stemmedQuery = stemmer.stem(stemmedQuery)

        # String matching query dengan array of commands
        for cmd in command:
            if (KMPStringMatch(stemmedQuery, cmd)):
                break

        # Menambah task baru (poin 1)
        if (cmd == 'tambah' or cmd == "ingat" or cmd == 'ingetin'):
            
            # Pencarian keyword dengan regex
            matkul = searchKodeMatkul(query)
            topik = searchTopik(query)
            tanggal = searchTanggal(query)
            jenis = searchJenis(query)
            
            # Syarat untuk menambahkan task : ada matkul, topik, tanggal, dan jenis
            # Jika seluruh syarat terpenuhi
            if (matkul != None and topik != None and tanggal != None and jenis != None):

                # Memeriksa apakah tanggal valid
                if (isTanggalValid(tanggal[0])):

                    # Menambah task ke database
                    addTask(connection, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2], matkul, jenis, topik)

                    # Mengambil semua task yang ada di database
                    arr = getTaskAll(connection)
                    line = ""
                    
                    # Format output daftar semua task
                    for el in arr:
                        line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                    chat.append("[Task Berhasil Dicatat]<br>" + line)
                
                # Tanggal tidak valid
                else:  
                    chat.append("Tanggal tidak valid")

            # Jika ada syarat yang tidak terpenuhi  
            else:   
                error = ""
                if (matkul == None):
                    error += "Tidak ada kode matkul<br>"
                if (topik == None):
                    error += "Tidak ada topik tugas<br>"
                if (tanggal == None):
                    error += "Tidak ada tanggal tugas<br>"
                if (jenis == None):
                    error += "Tidak ada jenis tugas<br>"   

                # Menambahkan pesan error ke chat
                chat.append(error)    
        
        # Menampilkan deadline task (poin 2 dan 3)
        elif (cmd == 'deadline' or cmd == 'kumpul' or cmd == 'tenggat' or cmd == 'ngumpulin'):
            # Proses pencarian keyword menggunakan regex
            matkul = searchKodeMatkul(query)
            print(matkul)
            topik = searchTopik(query)
            print(topik)
            tanggal = searchTanggal(query)
            print(tanggal)
            tanggalRelatif = searchTanggalRelatif(query)
            print(tanggalRelatif)
            jenis = searchJenis(query)
            print(jenis)
            # Kasus general jika tidak dispecify topik, tanggal, tanggalRelatif, dan jenis tugas
            if (matkul == None and topik == None and tanggal == [] and tanggalRelatif == (None,None) and jenis == None):
                # fetch data dari database tasks
                temp = getTaskAll(connection)
                line = ""
                    
                # Memasukkan task ke dalam array of chats
                for el in temp:
                    line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                chat.append("[Daftar Deadline]<br>" + line)
                
            # based on tanggal atau period time
            elif ((matkul == None and topik == None) and (tanggal != [] or tanggalRelatif != (None,None))):
                # based on period (1 minggu, 2 hari, 3 bulan, etc)
                # Menghitung jumlah hari yang harus ditambah ke current date
                if (tanggal==[]):
                    satuan = tanggalRelatif[1]
                    durasi = int(tanggalRelatif[0])
                    if (satuan == "minggu"):
                        durasi *= 7
                    elif (satuan == "bulan"):
                        durasi *= 30
                    # Menghitung tanggal relatif
                    tglAkhir = datetime.now()
                    tglAkhir = tglAkhir + timedelta(days=durasi)
                    if (jenis == None):
                        # Fetch data dari database tasks
                        temp = getTaskByPeriod(connection, datetime.now().day, datetime.now().month , datetime.now().year, tglAkhir.day, tglAkhir.month , tglAkhir.year)
                    else :
                        temp = getTaskByPeriodType(connection, datetime.now().day, datetime.now().month , datetime.now().year, tglAkhir.day, tglAkhir.month , tglAkhir.year, jenis)
                    line = ""
                    # Memasukkan task ke dalam array of chats
                    for el in temp:
                        line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                    chat.append("[Daftar Deadline]<br>" + line)
                # based on tanggal
                elif(tanggalRelatif==(None,None)):
                    # based on range 2 tanggal 
                    if (len(tanggal)==2):
                        if (jenis==None):
                            # Fetch data dari database tasks
                            temp = getTaskByPeriod(connection, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2], tanggal[1][0], convertBulanToInt(tanggal[1][1]), tanggal[1][2])            
                        else :
                            temp = getTaskByPeriodType(connection, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2], tanggal[1][0], convertBulanToInt(tanggal[1][1]), tanggal[1][2], jenis)
                        line = ""
                        # Memasukkan task ke dalam array of chats
                        for el in temp:
                            line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                        chat.append("[Daftar Deadline]<br>" + line)
                    #based on 1 tanggal
                    elif (len(tanggal)==1):
                        if (jenis == None):
                            # Fetch data dari database tasks
                            temp = getTaskByExactDate(connection, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2])
                        else :
                            temp = getTaskByExactDateType(connection, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2], jenis)
                        line = ""
                        # Memasukkan task ke dalam array of chats
                        for el in temp:
                            line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                        chat.append("[Daftar Deadline]<br>" + line)
            # based on matkul atau jenis kata penting
            elif (topik == None and tanggal == [] and tanggalRelatif == (None,None)) and (matkul != None or jenis!= None):
                if (matkul==None):
                    # Fetch data dari database tasks
                    temp = getTaskByType(connection,jenis)
                    line = ""
                    # Memasukkan task ke dalam array of chats
                    for el in temp:
                        line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                    chat.append("[Daftar Deadline]<br>" + line)
                elif(jenis==None):
                    # Fetch data dari database tasks
                    temp = getTaskByMatkul(connection,matkul)
                    line = ""
                    # Memasukkan task ke dalam array of chats
                    for el in temp:
                        line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                    chat.append("[Daftar Deadline]<br>" + line)
                else:
                    # Fetch data dari database tasks
                    temp = getTaskByMatkulType(connection,matkul,jenis)
                    line = ""
                    # Memasukkan task ke dalam array of chats
                    for el in temp:
                        line += "(ID: " + str(el[0]) + ") " + str(el[1]) + " - " + str(el[2]) + " - " + str(el[3]) + " - " + str(el[4]) + "<br>"
                    chat.append("[Daftar Deadline]<br>" + line)
                       
        # Memperbarui deadline task tertentu (poin 4)
        elif (cmd == 'update' or cmd == 'ubah' or cmd == 'undur' or cmd == 'maju' or cmd == 'baharu' or cmd == 'baru'):
            
            # Pencarian keyword dengan regex
            id = searchID(query)
            tanggal = searchTanggal(query)
            
            # Syarat terpenuhi: query mengandung id dan tanggal yang valid
            if (id != None and tanggal != [] and int(id) > 0 and int(id) <= getMaxId(connection) and isTanggalValid(tanggal[0])):

                # Update database
                updateTaskDeadline(connection, id, tanggal[0][0], convertBulanToInt(tanggal[0][1]), tanggal[0][2])
                # Pesan berhasil
                chat.append("Deadline task " + id + " berhasil diperbarui.")

            # Syarat tidak terpenuhi
            else:
                error = ""
                # Tidak ada id
                if (id == None):
                    error += "Tidak ada ID task<br>"
                # Id tidak valid (berada di luar range id dalam database)
                elif (int(id) <= 0 or int(id) > getMaxId()):
                    error += "Task tersebut tidak ditemukan di daftar task<br>"
                # Tidak ada tanggal
                if (tanggal == []):
                    error += "Tidak ada tanggal<br>"
                # Tanggal tidak valid
                elif (not isTanggalValid(tanggal[0])):
                    error += "Tanggal tidak valid"
                # Menampilkan pesan error
                chat.append(error)
        
        # Selesai mengerjakan task (poin 5)
        elif (cmd == 'selesai' or cmd == 'kelar' or cmd == 'beres' or cmd == 'rampung'):
            
            # Pencarian keyword dengan regex
            id = searchID(query)

            # Syarat terpenuhi: query mengandung id yang valid
            if (id != None and int(id) > 0 and int(id) <= getMaxId(connection)):
                # Delete task dari database
                deleteTask(connection, id)
                # Pesan berhasil
                chat.append("Berhasil mengurangi kekeosan")

            # Syarat tidak terpenuhi
            else:
                # Tidak ada id
                if (id == None):
                    chat.append("Tidak ada ID task")
                # Id tidak valid
                elif (int(id) <= 0 or int(id) > getMaxId(connection)):
                    chat.append("Task tersebut tidak ditemukan di daftar task")

        # Menampilkan list of commands yang dapat dilakukan
        elif (cmd == 'help' or cmd == 'laku' or cmd == 'perintah' or cmd == 'bantu'):
            chat.append('''[Fitur]
            <br>1. Menambahkan task baru 
            <br>2. Melihat daftar task 
            <br>3. Menampilkan deadline task
            <br>4. Update task
            <br>5. Menandai task yang sudah selesai
            <br>
            <br>[Daftar kata penting]
            <br>1. Kuis
            <br>2. Ujian
            <br>3. Tucil
            <br>4. Tubes
            <br>5. Praktikum
            <br>6. Mummu
            ''')
        
        # Query dari user tidak valid 
        else:
            chat.append("Perintah tidak dikenali, tulis yang bener dong")
        
    return render_template("home.html", chat=chat, nchat=len(chat))


def convertBulanToInt(bulan):
    # Mengkonversi bulan supaya menjadi sesuai dengan format input ke dalam database 
    # Parameter : 
        # bulan : string
    if (bulan == '01' or bulan == '1' or bulan == "Januari" or bulan == "januari"):
        return '01'
    elif (bulan == '02' or bulan == '2' or bulan == "Februari" or bulan == "februari"):
        return '02'
    elif (bulan == '03' or bulan == '3' or bulan == "Maret" or bulan == "maret"):
        return '03'
    elif (bulan == '04' or bulan == '4' or bulan == "April" or bulan == "april"):
        return '04'
    elif (bulan == '05' or bulan == '5' or bulan == "Mei" or bulan == "mei"):
        return '05'
    elif (bulan == '06' or bulan == '6' or bulan == "Juni" or bulan == "juni"):
        return '06'
    elif (bulan == '07' or bulan == '7' or bulan == "Juli" or bulan == "juli"):
        return '07'
    elif (bulan == '08' or bulan == '8' or bulan == "Agustus" or bulan == "agustus"):
        return '08'
    elif (bulan == '09' or bulan == '9' or bulan == "September" or bulan == "september"):
        return '09'
    elif (bulan == '10' or bulan == "Oktober" or bulan == "oktober"):
        return '10'
    elif (bulan == '11' or bulan == "November" or bulan == "november"):
        return '11'
    elif (bulan == '12' or bulan == "Desember" or bulan == "desember"):
        return '12'

def isTanggalValid(tanggal):
    # Pemeriksaan tanggal yang sesuai dengan kaidah kalender masehi
    # Parameter :
        # tanggal : string  
    if (tanggal[1] == '4' or tanggal[1] == '04' or tanggal[1] == 'April' or tanggal[1] == 'april'
    or tanggal[1] == '6' or tanggal[1] == '06' or tanggal[1] == 'Juni' or tanggal[1] == 'juni'
    or tanggal[1] == '9' or tanggal[1] == '09' or tanggal[1] == 'September' or tanggal[1] == 'september'
    or tanggal[1] == '11' or tanggal[1] == 'November' or tanggal[1] == 'november'):
        if (tanggal[0] == '31'):
            return False
        else:
            return True
    elif (tanggal[1] == '2' or tanggal[1] == '02' or tanggal[1] == 'Februari' or tanggal[1] == 'februari'):
        if (int(tanggal[2]) % 4 == 0):
            if (int(tanggal[2]) % 100 == 0):
                if (int(tanggal[2]) % 400 == 0):
                    if (int(tanggal[0]) > 29):
                        return False
                    else:
                        return True
                else:
                    if (int(tanggal[0]) > 28):
                        return False
                    else:
                        return True
            else:
                if (int(tanggal[0]) > 29):
                    return False
                else:
                    return True
        else:
            if (int(tanggal[0]) > 28):
                return False
            else:
                return True
    else:
        return True

# MAIN
if __name__ == "__main__":
    app.run(debug=True)
