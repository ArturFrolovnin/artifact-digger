#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "DiggingComponent.generated.h"


UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class ARCHEODIG_API UDiggingComponent : public UActorComponent
{
	GENERATED_BODY()

public:

	UDiggingComponent();


	// Главная функция копания.
	//
	// Сейчас вызывается каждый кадр из:
	//
	// Blueprint Event Tick
	//      ↓
	// Process Digging
	//
	// Но внутри самой функции уже есть DigInterval,
	// поэтому реальное копание не происходит каждый кадр.
	UFUNCTION(BlueprintCallable, Category = "Digging")
	void ProcessDigging();


	// --------------------------------------------------
	// Настройки копания
	// --------------------------------------------------


	// Радиус области, в которой удаляем voxel instances.
	//
	// Старое значение из Blueprint:
	// 65 см.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Digging")
	float DigRadius = 65.0f;


	// Минимальное время между двумя попытками копания.
	//
	// 0.25 = максимум примерно 4 копка в секунду.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Digging")
	float DigInterval = 0.25f;


	// Максимальное расстояние ОТ ПЕРСОНАЖА
	// до точки попадания.
	//
	// Это не длина Line Trace.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Digging")
	float DigReach = 350.0f;


	// Длина Line Trace от камеры.
	//
	// В старом Blueprint использовалось 800 см.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Digging")
	float TraceDistance = 800.0f;


	// Показывать debug Line Trace и точку попадания.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Digging|Debug")
	bool bDrawDebug = true;


private:

	// Время, после которого разрешён следующий копок.
	//
	// Например:
	//
	// текущее время = 10.0
	// DigInterval = 0.25
	//
	// NextDigTime станет 10.25.
	float NextDigTime = 0.0f;
};