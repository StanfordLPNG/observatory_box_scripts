#!/usr/bin/env python

import os
import sys
import argparse
from slack_post import slack_post
from os import path
from datetime import datetime
from subprocess import check_call


def main():
    local_sides = {
        'AWS Brazil': '52.67.203.197',
        'AWS California': '52.52.80.245',
        'AWS Korea': '52.79.43.78',
        'AWS India': '35.154.48.15',
    }

    remote_sides = {
        'Stanford': 'pi@171.66.3.65',
        'Brazil': 'pi@177.234.144.122',
        'Colombia': 'pi@138.121.201.58',
        'Mexico': 'pi@143.255.56.146',
        'China': 'yanyu@101.6.97.145',
        'Nepal': 'nepal6',  # uses ssh alias, currently only AWS India works
        'India': 'pi@109.73.164.122',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'local', choices=local_sides.keys(), help='local side')
    parser.add_argument(
        'remote', choices=remote_sides.keys(), help='remote side')
    parser.add_argument(
        '--run-times', metavar='TIMES', action='store', dest='run_times',
        type=int, default=1, help='run times of each test')
    parser.add_argument(
        '--sender-side', choices=['local', 'remote'], action='store',
        dest='sender_side', default='remote',
        help='the side to be data sender (default remote)')
    parser.add_argument(
        '--remote-interface', metavar='INTERFACE', action='store',
        dest='remote_if', help='remote interface to run tunnel on')
    args = parser.parse_args()


    if args.remote_if:
        remote_text = '%s %s' % (args.remote, args.remote_if)
    else:
        remote_text = args.remote

    if args.sender_side is 'remote':
        uploader = remote_text
        downloader = args.local
    else:
        uploader = args.local
        downloader = remote_text

    experiment_title = '%s to %s %d runs' % (uploader, downloader, args.run_times)

    slack_post('Running experiment uploading from ' + experiment_title + ".")

    test_dir = os.path.expanduser('~/pantheon/test/')
    os.chdir(test_dir)
    check_call('rm -rf *.log *.json *.png *.pdf *.out verus_tmp', shell=True)

    cmd = ('./run.py -r %s:~/pantheon -t 30 --tunnel-server local '
           '--local-addr %s --sender-side %s --local-info "%s" '
           '--remote-info "%s" --random-order --run-times %s'
           % (remote_sides[args.remote], local_sides[args.local],
              args.sender_side, args.local, args.remote, args.run_times))
    if args.remote_if:
        cmd += ' --remote-interface ' + args.remote_if

    sys.stderr.write(cmd + ' --run-only setup\n')
    check_call(cmd + ' --run-only setup', shell=True)

    sys.stderr.write(cmd + ' --run-only test\n')
    check_call(cmd + ' --run-only test', shell=True)

    date = datetime.utcnow()
    date = date.replace(microsecond=0).isoformat().replace(':', '-')

    src_dir = '%s-%s-logs' % (date, experiment_title.replace(' ', '-'))
    check_call(['mkdir', src_dir])
    check_call('cp *.log *.json ' + src_dir, shell=True)

    src_tar = src_dir + '.tar.xz'
    check_call('tar cJf ' + src_tar + ' ' + src_dir, shell=True)

    s3_folder = '/real-world-results/%s/' % args.remote
    s3_url = 's3://stanford-pantheon' + s3_folder + src_tar
    check_call('aws s3 cp ' + src_tar + ' ' + s3_url, shell=True)

    url = 'https://stanford-pantheon.s3.amazonaws.com' + s3_folder + src_tar
    slack_text = ("Logs archive of %s uploaded to <%s>\n"
                  "To generate report run: `pantheon/analyze/analyze.py "
                  "--s3-link %s`" % (experiment_title, url, url))
    slack_post(slack_text)

    sys.stderr.write('Logs archive uploaded to: %s\n' % url)
    check_call(['rm', '-rf', src_dir, src_tar])


if __name__ == '__main__':
    main()
