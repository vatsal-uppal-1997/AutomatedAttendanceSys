#!/usr/bin/python3
from isc_dhcp_leases import IscDhcpLeases
import pymysql
import threading
from threading import Thread
import datetime
from scapy.all import *
import getopt
import sys
import ipcalc


# noinspection PyBroadException
class MakeDb:
    def __init__(self, ip=None, teacher=None):
        self.ip = ip
        self.iface = 'wlan0'
        self.active = []
        self.blacklist = []
        self.working = []
        self.available_subnets = None
        self.target = None
        self.mutex = threading.Lock()
        self.teacher = teacher

    def read_conf(self):
        with open("subnets.conf") as source:
            data = source.read()
            x = data.replace('\t', ',')
            y = x.split('\n')
        self.available_subnets = list(set([tuple(k.split(',')) for k in y if k != '']))
        for x in self.available_subnets:
            localnet = ipcalc.Network(''.join(x))
            if self.ip in localnet:
                self.target = ''.join(x)
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
            print("timer {} timeout {} bool {}".format(time.time(), timeout, time.time() >= timeout))
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
        while True:
            if i <= 30:
                leases = IscDhcpLeases('/var/lib/dhcp/dhcpd.leases')
                get_valid = leases.get_current()
                all_leases = list(set([(value.ip, value.ethernet) for value in get_valid.values()]))
                check_subnet = list(set(filter(self.gen, all_leases)))
                print(i)
            else:
                pass
            self.active = list(set(filter(self.arp, check_subnet)))
            self.__print__()
            time.sleep(5)
            i += 1

    def __print__(self):
        db = pymysql.connect("localhost", "cereal", "toor", "register")
        cursor = db.cursor()
        tblname = self.teacher + "DATE" + str(''.join((str(datetime.date.today()).split('-'))))
        try:
            sql = '''CREATE TABLE {}DATE{} (IP varchar(20), MAC varchar(20), UNIQUE(IP, MAC))''' \
                .format(self.teacher, ''.join((str(datetime.date.today()).split('-'))))
            cursor.execute(sql)
        except:
            pass
        for x, y in self.active:
            try:
                sql = '''INSERT INTO {} VALUES ('{}', '{}')'''.format(tblname, x, y)
                cursor.execute(sql)
            except:
                pass
        if self.blacklist is not None:
            for x, y in self.blacklist:
                try:
                    sql = '''delete from {} where MAC="{}"'''.format(tblname, y)
                    cursor.execute(sql)
                except:
                    pass
        db.commit()
        db.close()


def usage():
    print("./mkdb --ip=192.168.100.1 --teacher=xyz")


def main():
    ip = None
    teacher = None
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "i:t:", ["ip=", "teacher="])
    except getopt.GetoptError as Error:
        print(Error)
        usage()
        sys.exit(2)
    for opts, args in options:
        if opts in ("-i", "--ip"):
            ip = str(args)
        else:
            teacher = str(args)
    instance = MakeDb(ip, teacher)
    instance.main()


if __name__ == "__main__":
    main()
