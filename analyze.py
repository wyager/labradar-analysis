#!/usr/bin/env python3

import csv
import sys
import os
import statistics

class Sample():
    def __init__(self, row):
        self.sec, self.fps, self.yds, self.snr = [float(x) if x != '-' else None for x in row]
    def __str__(self):
        return '{}s {}fps {}yd {}dB'.format(self.sec, self.fps, self.yds, self.snr)
        
class ShotRecord():
    def __init__(self, contents):
        sep, did, series, shot, blank, header, *entries = contents
        assert(sep == ['sep=',''])
        assert('Device ID' == did[0])
        self.did = did[1]
        assert('Series No' == series[0])
        self.series = int(series[1])
        assert('Shot No' == shot[0])
        self.shot = int(shot[1])
        assert([] == blank)
        assert(['Time (s)', 'Vel (fps)', 'Dist (yd)', 'SNR'] == header)
        self.samples = [Sample(entry) for entry in entries]
    def __str__(self):
        return 'di{} se{} sh{} {}...'.format(self.did, self.series, self.shot, ','.join(str(samp) for samp in self.samples[:2]))

if(len(sys.argv) < 3):
    print("Usage: analyze.py <path to SD card> <series number> <series number> ...")
    exit(1)
    
card = sys.argv[1]
seriess = sys.argv[2:]
records = []
for series in seriess:
    series = int(series)
    series_name = "SR{:0>4}".format(series)
    series_dir = card + "/LBR/" + series_name
    series_report = series_dir + "/" + series_name + " Report.csv"
    trk_dir = series_dir + "/TRK" 
    for shot_file in os.listdir(trk_dir):
        if not shot_file.endswith(".csv"):
            continue
        shot_file = trk_dir + "/" + shot_file
        with open(shot_file) as shot_file:
            records.append(ShotRecord(csv.reader(shot_file, delimiter=';')))
     
snr_cutoff = 20 
snr_discards = [r for r in records if r.samples[1].snr < snr_cutoff]
print("Discarding low-SNR samples: ")
for disc in snr_discards:
    print("  ", disc)

records = [r for r in records if r.samples[1].snr >= snr_cutoff]

inferred_speeds = [r.samples[0].fps for r in records]

median_speed = statistics.median(inferred_speeds) 

min_speed = median_speed * 0.95
max_speed = median_speed * 1.05

speed_discards = [r for r in records if (r.samples[0].fps < min_speed or r.samples[0].fps > max_speed)]
print("Discarding wild speeds: ")
for disc in speed_discards:
    print("  ", disc)

records = [r for r in records if not (r.samples[0].fps < min_speed or r.samples[0].fps > max_speed)]

print("{} records remaining after filtering".format(len(records)))
inferred_speeds = sorted([r.samples[0].fps for r in records])
median_speed = statistics.median(inferred_speeds) 
print("Median {}fps".format(median_speed))
avg_speed = statistics.mean(inferred_speeds)
print("Avg {}fps".format(avg_speed))
stddev_speed = statistics.stdev(inferred_speeds)
print("Stddev {}fps".format(stddev_speed))
deciles = statistics.quantiles(inferred_speeds, n=10)
decile_diffs = [(deciles[i+1] - deciles[i], i) for i in range(len(deciles)-1)]
decile_maxjump, maxjump_start = max(decile_diffs)
print("Deciles: " + str(deciles))
print("Max jump: {} @ {}%".format(decile_maxjump,(maxjump_start + 2) * 10 - 5))
minimum = min(inferred_speeds)
maximum = max(inferred_speeds)
print("Min: {} Max: {}".format(minimum, maximum))


    
    
