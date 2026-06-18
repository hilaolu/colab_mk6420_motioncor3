rm -rf MotionCor3
git clone https://github.com/hilaolu/MotionCor3.git
cd MotionCor3

# Precise patch for the linking step in makefile11
sed -i 's/@$(NVCC) -g -G -m64 $(OBJS)/@$(NVCC) -g -G -m64 -Xlinker -no-pie $(OBJS)/' makefile11

# Build with correct CUDA path
make exe -f makefile11 CUDAHOME=/usr/local/cuda


cd ..

curl -L -O ftp://ftp.ebi.ac.uk/empiar/world_availability/12870/data/RAW_Tif/K319040035GainRefx1m3kv300.mrc
