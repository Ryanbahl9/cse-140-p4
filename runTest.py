import os
import subprocess


values = []
for runDist in range(0, 5):
    for enemyDistWeight in range(-10, 5, 5):
        print(str(runDist) + ' ' + str(enemyDistWeight))
        out = subprocess.Popen(['python3', '-m', 'pacai.bin.capture', '--num-games', '10', '--null-graphics', '--red', 'pacai.student.myTeam', '--red-args', 'runDist=5,enemyDistWeight=-10', '-q'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT)

        stdout,stderr = out.communicate()
        values.append((float(stdout.split()[0]), (runDist, enemyDistWeight)))


values.sort(reverse=True)
if values:
    print(values[0])
else:
    print('UR DUMB')