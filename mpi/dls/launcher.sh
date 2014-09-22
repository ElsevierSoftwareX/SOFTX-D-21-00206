module load global/cluster

qsub -sync y -j y -pe openmpi 8 -q medium.q@@com01 /home/ssg37927/Savu/mpi/dls/mpijob.sh $@ > tmp.txt

filename=`echo mpijob.sh.o`
jobnumber=`awk '{print $3}' tmp.txt | head -n 1`
filename=$filename$jobnumber

while [ ! -f $filename ]
do
  sleep 2
done

cat $filename

sleep 20
echo qacct -j ${jobnumber}
qacct -j ${jobnumber}