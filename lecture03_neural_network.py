import tensorflow as tf
import pandas as pd

data = pd.read_csv('gpascore.csv')
print(data)
exit()

model = tf.keras.models.Sequencial([
    tf.keras.layers.Dense(64, activation='sigmoid'),
    tf.keras.layers.Dense(128, activation='sigmoid'),
    tf.keras.layers.Dense(1, activation='sigmoid'),
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#model.fit(입력 데이터, 출력 데이터, epochs=10)
