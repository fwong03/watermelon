def get_rid_of_duplicates(file_path):
    dict_of_zips = {}
    for row in open(file_path):
        row.strip()
        temp = row.split(',')
        zipcode = int(temp[2])
        lat = temp[3]
        longide = temp[4]
        dict_of_zips[zipcode] = (lat, longide)

    return dict_of_zips

def write_to_new_file(file_path, zips_to_add):
    target = open(file_path, 'w')
    target.truncate()

    for zipcode in zips_to_add:
        line = str(zipcode) + '|' + zips_to_add[zipcode][0] + '|' + zips_to_add[zipcode][1]
        target.write(line)
        target.write("\n")



dict_of_zips = get_rid_of_duplicates('data/cityzip')

write_to_new_file('data/cityzip_nodupes', dict_of_zips)

