from __future__ import annotations

import os
from pathlib import Path

import tensorflow as tf


def make_datasets(data_root: Path, image_size: tuple[int, int], batch_size: int):
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_root / "train",
        seed=42,
        image_size=image_size,
        batch_size=batch_size,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_root / "val",
        seed=42,
        image_size=image_size,
        batch_size=batch_size,
    )
    test_ds = tf.keras.utils.image_dataset_from_directory(
        data_root / "test",
        seed=42,
        image_size=image_size,
        batch_size=batch_size,
        shuffle=False,
    )
    return train_ds, val_ds, test_ds


def build_model(num_classes: int) -> tf.keras.Model:
    data_augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(0.12),
            tf.keras.layers.RandomContrast(0.15),
        ]
    )

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.SparseTopKCategoricalAccuracy(k=3, name="top3_accuracy"),
        ],
    )
    return model


def main() -> None:
    data_root = Path("data/processed")
    if not data_root.exists():
        raise FileNotFoundError("data/processed not found. Run scripts/prepare_dataset.py first.")

    train_ds, val_ds, test_ds = make_datasets(data_root, image_size=(224, 224), batch_size=32)
    class_names = train_ds.class_names
    model = build_model(num_classes=len(class_names))

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(
            "artifacts/best_model.keras", save_best_only=True, monitor="val_loss"
        ),
    ]

    Path("artifacts").mkdir(exist_ok=True)

    epochs = int(os.getenv("EPOCHS", "12"))
    model.fit(train_ds, validation_data=val_ds, epochs=epochs, callbacks=callbacks)
    eval_metrics = model.evaluate(test_ds, return_dict=True)
    print(f"Test metrics: {eval_metrics}")

    model.save("artifacts/final_model.keras")
    with open("artifacts/class_names.txt", "w", encoding="utf-8") as class_file:
        for name in class_names:
            class_file.write(f"{name}\n")


if __name__ == "__main__":
    main()
