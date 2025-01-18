import tensorflow as tf
import matplotlib.pyplot as plt

# trainX: 트레이닝용 입력 데이터
# trainY: 트레이닝용 출력 데이터(정답)
# testX: 테스트용 입력 데이터
# testY: 테스트용 출력 데이터(정답)
((trainX, trainY), (testX, testY)) = tf.keras.datasets.fashion_mnist.load_data() 
print(trainX[0])
print(trainX.shape)
print(trainY)

class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, input_shape=(28, 28), activation="relu"),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax"),
    ])
# model의 outline 출력하기
# model 에 input_shape을 지정해줘야 한다.
model.summary()

exit()

# relu: activation function 음수는 0으로 만드는 함수
# cross entropy loss function 사용 확률예측문제일때
# sigmoid: 결과를 0~1로 압축 binary 예측문제에 사용 대학원에 붙는다/안붙는다.

# category 예측문제일 때 softmax
# category 예측문제일 때 loss function: sparse_categorical_crossentropy

model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=['accuracy'])
model.fit(trainX, trainY, epochs=5)
