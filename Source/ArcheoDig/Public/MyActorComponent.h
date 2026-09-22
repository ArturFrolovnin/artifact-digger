#pragma once

// Базовые типы Unreal Engine:
// FString, FVector, FColor и много чего ещё.
#include "CoreMinimal.h"

// Базовый класс компонента.
// Наш MyActorComponent будет наследоваться от UActorComponent.
#include "Components/ActorComponent.h"

// Этот файл создаёт Unreal Header Tool.
// Он нужен для UCLASS, UFUNCTION, UPROPERTY и Blueprint.
// Важно: этот include обычно должен быть последним.
#include "MyActorComponent.generated.h"


// Говорим Unreal, что это Unreal-класс.
// BlueprintSpawnableComponent позволяет добавлять этот компонент
// в Blueprint через кнопку Add Component.
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class ARCHEODIG_API UMyActorComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	// Конструктор компонента.
	// Вызывается при создании объекта этого класса.
	UMyActorComponent();

	// Делаем C++ функцию доступной в Blueprint как обычную ноду.
	// Category определяет, в какой категории она будет отображаться.
	UFUNCTION(BlueprintCallable, Category = "C++ Test")
	void ShowHelloWorld();
};