import tensorflow as tf
import pandas as pd # 파일을 불러오기 위한 library

tall = [170, 180, 175, 160]
shoe = [260, 270, 265, 255]

a = tf.Variable(0.1)
b = tf.variable(0.2)

opt = tf.keras.optimizers.Adam(learning_rate = 0.1))
#경사하강법을 사용해서 변수를 업데이트하는 도구
def lossF():
    return tf.square(실제값 - 예측값)
opt.minimize(lossF, var_list[a, b]))
