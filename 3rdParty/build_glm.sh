
git clone https://github.com/g-truc/glm.git

cd glm/

mkdir build && cd build

cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . -j$(nproc)

make install