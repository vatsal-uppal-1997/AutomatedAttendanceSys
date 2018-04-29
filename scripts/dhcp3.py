from threading import Thread
import threading
import pymysql
import datetime
from scapy.all import *
from isc_dhcp_leases import IscDhcpLeases


class Attendance:

    def __init__(self, iface=None, teacher=None):
        self.iface = iface
        self.Teacher = teacher
        self.active = []
        self.blacklist = []
        self.active_thread = []
        self.workers = ["worker-1", "worker-2", "worker-3", "worker-4"]
        self.queue = queue.Queue(108)
        self.mutex = threading.Lock()

    def __arp__(self):
        conf.verb = 0
        self.mutex.acquire()
        preserve_dest = None
        self.mutex.release()

        while True and (not self.queue.empty() or preserve_dest is not None):

            self.mutex.acquire()
            dest = self.queue.get()
            if dest in self.blacklist:

                self.mutex.release()
                break

            elif self.queue.empty and preserve_dest is not None:

                dest = preserve_dest
            self.mutex.release()
    #        print(f"Working on {dest}")
            count = 0

            answered, unanswered = srp(Ether(dst=dest[1]) / ARP(pdst=dest[0]), timeout=2, inter=0.1, iface=self.iface)

            for sent, received in answered:

                if received.sprintf("%Ether.src%") == dest[1]:
                    self.mutex.acquire()
                    self.active.append(dest)
                    self.active = list(set(self.active))
                    self.mutex.release()
                    return
            time.sleep(12)
            self.mutex.acquire()
            count += 1
            self.mutex.release()
            if count != 2:

                self.mutex.acquire()
                self.blacklist.append(dest)
                self.blacklist = list(set(self.blacklist))
                self.mutex.release()
                break

            else:

                self.mutex.acquire()
                preserve_dest = dest
                self.mutex.release()
                continue

    def __driver__(self):
        Flag = True
        count = 0
        ip_mac = None
        while True:
            while Flag:
                leases = IscDhcpLeases('/var/lib/dhcp/dhcpd.leases')
                get_lease_object = leases.get()

                ip_mac = list(set([(x.ip, x.ethernet) for x in get_lease_object]))
                time.sleep(10)
                count+=1
                if count == 6:
                    Flag = False

            for x in ip_mac:
                self.queue.put(x)

            for x in self.active_thread:
                x.join()

            for x in self.workers:
                make_worker = Thread(target=self.__arp__, name=x)
                make_worker.start()
                self.active_thread.append(make_worker)

            print(bcolors.OKGREEN+str(self.active)+bcolors.ENDC+"\n")
            print(bcolors.OKGREEN+str(self.blacklist)+bcolors.ENDC+"\n")
            self.__print__()
            time.sleep(20*60)

    def __print__(self):
        db = pymysql.connect("localhost","cereal", "toor", "register")
        cursor = db.cursor()
        tblname = self.Teacher+"DATE" + str(''.join((str(datetime.date.today()).split('-'))))
        try:
            sql = '''CREATE TABLE {}DATE{} (IP varchar(20), MAC varchar(20), UNIQUE(IP, MAC))'''\
                    .format(self.Teacher, ''.join((str(datetime.date.today()).split('-'))))
            cursor.execute(sql)
        except:
            pass
        for x, y in self.active:
            try:
                sql = '''INSERT INTO {} VALUES ('{}', '{}')'''.format(tblname, x, y)
                cursor.execute(sql)
            except:
                pass
        for x, y in self.blacklist:
            try:
                sql = '''delete from {} where MAC="{}"'''.format(tblname, y)
                cursor.execute(sql)
            except:
                pass
        db.commit()
        db.close()


def main():
    teacher = input("ENTER TEACHER'S NAME (CamelCasing please) -> ")
    obj = Attendance(iface='wlan0', teacher=teacher)
    obj.__driver__()


if __name__ == "__main__":
    main()
