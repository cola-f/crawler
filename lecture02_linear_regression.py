import tensorflow as tf

train_x = [1,2,3,4,5,6,7]
train_y = [3,5,7,9,11,13,15]


a = tf.Variable(0.1) #초기값 randomize하는 것이 좋다.
b = tf.Variable(0.1)

def 손실함수(a, b):
    예측_y = train_x*a+b
    #차이^2+차이^2+차이^2 등등
    return tf.keras.losses.mse(train_y, 예측_y)

opt = tf.keras.optimizers.Adam(learning_rate=0.01)

for i in range(3000):
    opt.minimize(lambda: 손실함수(a, b) , var_list = [a,b])
    print(a.numpy(), b.numpy())

