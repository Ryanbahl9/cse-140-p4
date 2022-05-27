import os
import subprocess


values = []
for runDist in range(2, 16, 2):
    for enemyDistWeight in range(-100, 0, 10):
        print(str(runDist) + ' ' + str(enemyDistWeight))
        args = 'runDist=' + str(runDist) + ',enemyDistWeight=' + str(enemyDistWeight)
        out = subprocess.Popen(['python3', '-m', 'pacai.bin.capture', '--num-games', '10', '--null-graphics', '--red', 'pacai.student.myTeam', '--red-args', args, '-q'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)

        stdout,stderr = out.communicate()
        values.append((float(stdout.split()[0]), (runDist, enemyDistWeight)))


values.sort(reverse=True)
if values:
    print(values[0])
else:
    print('UR DUMB')