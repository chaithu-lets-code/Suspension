 #!/usr/bin/env python3

import subprocess
import getpass
from json import loads
import argparse
from prettytable import PrettyTable
import multiprocessing
from nie.db import netarch
import time


def get_ecors_under_ldap(ldap):
    engine = netarch.engine(query={'charset': 'utf8'}, user='phpview')
    query = '''
    select 
        DISTINCT geo.nie_name, 
        geo.nie_login, 
        geo.ecor_number, 
        e.ECOR_NAME, 
        e.ECOR_ID, 
        e.ECOR_TYPE 
    from 
        nie.gator_ecor_owners geo 
        inner join CMN_INT.AK_ECOR e on e.ECOR_NUMBER = geo.ecor_number 
        inner join CMN_INT.AK_REGION r on e.ECOR_ID = r.ECOR_ID 
    where 
        geo.nie_login = '{ldap}' 
        and e.STATUS = 'Live'
    '''.format(ldap=ldap)

    result = engine.execute(query)
    result = result.fetchall()
    return result


def get_user(cmd):
    try:
        out = subprocess.getoutput(cmd)
        #print(cmd)
        return out
    except:
        pass


def get_ecors(lst):
    return [item[3] for item in lst]


def get_ecors_cmd(cmd, ecors):
    return [cmd + ecor for ecor in ecors]

# x = threading.Thread(target=get_ecors_under_ldap,args=())
# print(threading.active_count())
# print(threading.enumerate())
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='This is for region suspension')

    parser.add_argument(

        'suspension_type',
        choices=['region', 'region_v6', 'machine'],
        type=str,
        help='to selet values for regions'
    )

    ARGS = parser.parse_args()
    cmd = "suspendtell -a "
    ecors = get_ecors(get_ecors_under_ldap(getpass.getuser()))
    ecors_cmd = get_ecors_cmd(cmd, ecors)

    # using spawn rather than fork
    multiprocessing.set_start_method('spawn')

    table = PrettyTable()

    table.field_names = (['Ecorname', 'target', 'network', 'target_type', 'ticket', 'reason'])
    print("checking the suspensions under",getpass.getuser().upper()," accounts")
    print("Script is running background.. Look at distant object in the window . . .")
    start_time=time.time()
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()) #taking maximum cpu threads automatically

    cmd_runs = pool.map(
        get_user,
        ecors_cmd
    )

    pool.close()
    pool.join()
    end_time=time.time()

    for ecor, cmd_run in zip(ecors, cmd_runs):

        if 'Warning:' in cmd_run:
            continue

        else:
            for row in loads(cmd_run)['matches']:

                if ARGS.suspension_type == row['target_type']:

                    table.add_row(
                        [ecor, row['target'], row['network_name'], row['target_type'], row['ticket'], row['reason']])
    print()
    print(table)
    print("Time Elapsed:", round(end_time-start_time), "[secs..]") 
