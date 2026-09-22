// Подключаем описание нашего DiggingComponent.
#include "DiggingComponent.h"

// Нужен для GEngine,
// через который можем вывести текст прямо на экран.
#include "Engine/Engine.h"


// Конструктор компонента.
UDiggingComponent::UDiggingComponent()
{
	// Сам компонент пока НЕ должен иметь собственный Tick.
	//
	// На данном этапе Tick будет находиться в Blueprint
	// и вызывать нашу C++ функцию ProcessDigging().
	PrimaryComponentTick.bCanEverTick = false;
}


// Эта функция будет вызываться из Blueprint.
void UDiggingComponent::ProcessDigging()
{
	if (GEngine)
	{
		// 1001 — ID сообщения.
		//
		// Поскольку ProcessDigging будет вызываться каждый кадр,
		// мы НЕ хотим создавать тысячи новых сообщений.
		//
		// Один и тот же ID заставляет Unreal
		// обновлять существующее сообщение.
		GEngine->AddOnScreenDebugMessage(
			1001,
			1.0f,
			FColor::Yellow,
			TEXT("ProcessDigging работает из C++")
		);
	}
}