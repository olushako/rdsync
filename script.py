import requests, os
import datetime, schedule, time

refresh_period = int(os.environ['REFRESH_INTERVAL']) 
apitoken = str(os.environ['API_TOKEN'])

def difference(string1, string2):
  string1 = string1.split('/')
  string2 = string2.split('/')

  A = set(string1)
  B = set(string2)

  str_diff = A.symmetric_difference(B)
  isEmpty = (len(str_diff) == 0)
 
  if isEmpty:
    return None
  else:
    return str_diff

def connected_to_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False

def refresher():

    if (not connected_to_internet('https://api.real-debrid.com')): 
        print ('No internet connection')
        return

    print (' - Iteration - ')

    headers = {'Authorization': f'Bearer {apitoken}'}
    folder = '/streams'
    # Get List of torrents
    data = {'offset': 0, 'page':0, 'limit': 100, 'filter': 'downloaded'}
    r = requests.get('https://api.real-debrid.com/rest/1.0/torrents', data = data, headers = headers)
    links = list()
    linkdata = r.json()
    for t in linkdata:
        if t['status']=='downloaded':
            for l in t['links']:
                links.append (l)
    # Unrestrict links
    portfolio = {}
    for link in links:
        data = {'link': link, 'password':''}
        r = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link', data = data, headers = headers)
        linkdata = r.json()
        if 'error_code' in linkdata:
            continue
        if str(linkdata['download']).lower().endswith(('.mkv', '.mp4', '.avi', '.m4v')):
            fname = linkdata['filename'].lower()
            fname = fname.replace('.mkv','.strm')
            fname = fname.replace('.mp4','.strm')
            fname = fname.replace('.avi','.strm')
            fname = fname.replace('.m4v','.strm')
            portfolio.update({fname:linkdata['download']})

    remove_counter = 0
    files = next(os.walk(folder))[2]
    for file in files: 
        if file not in portfolio.keys():
            os.remove(folder+ "/" + file)
            remove_counter=remove_counter+1

    added_counter = 0
    update_counter = 0
    # update streams repo
    for file in portfolio.keys():
        if not os.path.isfile(folder + "/" + file):
            with open(folder + "/" + file, 'a') as the_file:
                the_file.write(portfolio[file]) 
                added_counter=added_counter+1
        else: 
            f = open(folder + "/" + file,"r")
            lines = f.readlines()
            for line in lines:
                if (portfolio[file] not in line):
                    f.close()
                    f = open (folder + "/" + file,"w")
                    f.write(portfolio[file]) 
                    f.close()
                    print ('Updated. Difference: '+ difference(line, portfolio[file])+ ': ' +file)
                    update_counter=update_counter+1
                    break

    if added_counter!=0 or remove_counter!=0 or update_counter!=0:
        time = str(datetime.datetime.now())
        msg = f'{time}\tRemoved: {remove_counter}, Added: {added_counter}, Updated: {update_counter}'
        print (msg)

print ('--- CONTAINER STARTED ---')
schedule.every(refresh_period).minutes.do(refresher)

while True:
    schedule.run_pending()
    time.sleep(60)
