import tensorflow as tf

((trainX, trainY), (testX, testY)) = tf.keras.datasets.fashion_mnist.load_data() 

print(trainX.shape)
