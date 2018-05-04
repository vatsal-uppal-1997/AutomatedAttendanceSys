#!/usr/bin/python3
from isc_dhcp_leases import IscDhcpLeases
import pymysql
import threading
from threading import Thread
import datetime
from scapy.all import *
import argparse
import ipcalc


# noinspection PyBroadException
class MakeDb:
    def __init__(self, ip=None, teacher=None, section=None, app_timeout=25):
        self.ip = ip
        self.iface = 'wlan0'
        self.active = []
        self.blacklist = []
        self.working = []
        self.available_subnets = None
        self.target = None
        self.mutex = threading.Lock()
        self.teacher = teacher
        self.section = section
        self.app_timeout = app_timeout
        self.mac_db = ()

    def read_conf(self):
        with open("subnets.conf") as source:
            data = source.read()
            x = data.replace('\t', ',')
            y = x.split('\n')
        self.available_subnets = list(set([tuple(k.split(',')) for k in y if k != '']))
        for x in self.available_subnets:
            localnet = ipcalc.Network(x[0]+x[1])
            if self.ip in localnet:
                self.iface = x[2]
                self.target = ''.join(x[0]+x[1])
                break

    def gen(self, ip):
        localnet = ipcalc.Network(self.target)
        if ip[0] in localnet:
            return True
        else:
            return False

    def arp(self, ip):
        conf.verb = 0
        print("active worker "+str(self.working))
        answered, unanswered = srp(Ether(dst=ip[1]) / ARP(pdst=ip[0]), timeout=2, inter=0.1, iface=self.iface)
        for sent, received in answered:
            if received.sprintf("%Ether.src%") == ip[1]:
                return True
        if ip is not None and ip not in self.working and ip not in self.blacklist:
            make_worker = Thread(target=self.timer, name=ip[0], args=[ip])
            self.working.append(ip)
            make_worker.daemon = True
            make_worker.start()

    def timer(self, ip):
        timeout = time.time() + 60 * 2
        while True:
            print(f"timeout in ({(timeout-time.time())/60} mins)")
            if time.time() >= timeout:
                self.working.pop()
                break
            if ip in self.active:
                self.working.pop()
                return
            time.sleep(1)
        self.mutex.acquire()
        self.blacklist.append(ip)
        self.blacklist = list(set(self.blacklist))
        self.mutex.release()
        return

    def main(self):
        self.read_conf()
        check_subnet = []
        i = 0
        print(self.iface)
        timeout = time.time() + 60*self.app_timeout
        if self.app_timeout > 20:
            scan = time.time() + 60*(self.app_timeout/5)
        else:
            scan = time.time() + 60*(self.app_timeout/2)
        while True:
            if time.time() <= scan:
                leases = IscDhcpLeases('/var/lib/dhcp/dhcpd.leases')
                get_valid = leases.get_current()
                all_leases = list(set([(value.ip, value.ethernet) for value in get_valid.values()]))
                check_subnet = list(set(filter(self.gen, all_leases)))
                print(f"Discovered [{len(check_subnet)}]")
                print(f"Scan Time Left ({(scan-time.time())/60} minutes)")
                time.sleep(2)
            else:
                self.active = list(set(filter(self.arp, check_subnet)))
                self.__print__()
                time.sleep(5)
                i += 1
            if time.time() >= timeout:
                break
        return 0

    def __print__(self):
        db = pymysql.connect("localhost", "cereal", "toor", "website")
        cursor = db.cursor()
        # tblname = self.teacher + " section " + self.section + " date " + str(datetime.date.today())
        # try:
        #     #create table test (IP varchar(20), MAC varchar(20), UNIQUE(IP,MAC), FOREIGN KEY (mac) REFERENCES students(mac))
        #
        #     sql = '''CREATE TABLE `{}` (`IP` varchar(20), `MAC` varchar(20) PRIMARY KEY, UNIQUE(IP, MAC), FOREIGN KEY (mac) REFERENCES students(mac))''' \
        #         .format(tblname)
        #     cursor.execute(sql)
        # except:
        #     pass
        # for x, y in self.active:
        #     try:
        #         sql = '''INSERT INTO `{}` VALUES ('{}', '{}')'''.format(tblname, x, y)
        #         cursor.execute(sql)
        #     except:
        #         pass
        # if self.blacklist is not None:
        #     for x, y in self.blacklist:
        #         try:
        #             sql = '''delete from `{}` where MAC="{}"'''.format(tblname, y)
        #             cursor.execute(sql)
        #         except:
        #             pass
        # db.commit()
        # db.close()
        table_name = self.teacher + " section " + self.section + " date " + str(datetime.date.today())
        sql = '''select mac from students'''
        cursor.execute(sql)
        mac_db = cursor.fetchall()
        mac_db = tuple(i for i in mac_db)
        self.mac_db = tuple(j for i in mac_db for j in i)
        print(self.mac_db)
        try:
            sql = '''CREATE TABLE `{}` (`ID` VARCHAR(11), `NAME` VARCHAR(100), `SECTION` VARCHAR(10), `MAC` VARCHAR(20) PRIMARY KEY)'''.\
                format(table_name)
            cursor.execute(sql)
        except:
            pass
        for x, y in self.active:
            try:
                print(self.mac_db)
                print(y)
                if y in self.mac_db:
                    sql = '''SELECT id,name,section FROM students where mac="{}"'''.format(y)
                    cursor.execute(sql)
                    insert_data = cursor.fetchall()
                    for data in insert_data:
                        sql = '''INSERT INTO `{}` VALUES ("{}","{}","{}","{}")'''.format(table_name,
                                                                                         data[0], data[1], data[2], y)
                        cursor.execute(sql)
            except:
                pass
        if self.blacklist is not None:
            try:
                for x, y in self.blacklist:
                    sql = '''delete from `{}` where mac="{}"'''.format(table_name, y)
                    cursor.execute(sql)
            except:
                pass
        db.commit()
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="Enter Your local IP Address")
    parser.add_argument("teacher", help="Enter your name plus the section number\
     to take attendance of (example someteacher22)")
    parser.add_argument("section", help="Enter Section")
    arguments = parser.parse_args()
    ip = arguments.ip
    teacher = arguments.teacher
    section = arguments.section
    instance = MakeDb(str(ip), str(teacher), str(section), 1)
    instance.main()


def module(ip=None, teacher=None, section=None, timeout=None):
    instance = MakeDb(str(ip), str(teacher), str(section), int(timeout))
    return instance


if __name__ == "__main__":
    main()
