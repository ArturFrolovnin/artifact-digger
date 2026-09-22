// Подключаем описание нашего класса.
#include "MyActorComponent.h"

// Нужен для GEngine и вывода текста прямо на экран.
#include "Engine/Engine.h"


// Реализация конструктора.
UMyActorComponent::UMyActorComponent()
{
	// Нам не нужно выполнять этот компонент каждый кадр.
	// Поэтому Tick отключаем.
	PrimaryComponentTick.bCanEverTick = false;
}


// Реализация нашей функции ShowHelloWorld.
void UMyActorComponent::ShowHelloWorld()
{
	// Проверяем, что объект движка существует.
	if (GEngine)
	{
		// Выводим текст прямо на экран игры.
		GEngine->AddOnScreenDebugMessage(
			-1,                         // -1 = добавить новое сообщение
			3.0f,                       // показывать 3 секунды
			FColor::Green,              // цвет текста
			TEXT("Hello----55555-!") // сам текст
		);
	}

	// Дополнительно пишем то же сообщение в Unreal Output Log.
	UE_LOG(
		LogTemp,
		Warning,
		TEXT("Hello========!")
	);
}