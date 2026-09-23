#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TriggerLightActor.generated.h"


class USceneComponent;
class UBoxComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UPrimitiveComponent;


UCLASS()
class ARCHEODIG_API ATriggerLightActor : public AActor
{
	GENERATED_BODY()


public:

	ATriggerLightActor();


protected:

	// Вызывается, когда кто-то входит в TriggerBox.
	UFUNCTION()
	void OnTriggerBeginOverlap(
		UPrimitiveComponent* OverlappedComponent,
		AActor* OtherActor,
		UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex,
		bool bFromSweep,
		const FHitResult& SweepResult
	);


	// Вызывается, когда кто-то выходит из TriggerBox.
	UFUNCTION()
	void OnTriggerEndOverlap(
		UPrimitiveComponent* OverlappedComponent,
		AActor* OtherActor,
		UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex
	);


private:

	// Корневой компонент Actor.
	UPROPERTY(VisibleAnywhere, Category = "Trigger Light")
	USceneComponent* Root;


	// Видимая пластина на полу.
	UPROPERTY(VisibleAnywhere, Category = "Trigger Light")
	UStaticMeshComponent* PlateMesh;


	// Невидимая область,
	// которая определяет вход/выход игрока.
	UPROPERTY(VisibleAnywhere, Category = "Trigger Light")
	UBoxComponent* TriggerBox;


	// Куб, который будет стоять рядом.
	UPROPERTY(VisibleAnywhere, Category = "Trigger Light")
	UStaticMeshComponent* CubeMesh;


	// Источник света возле куба.
	UPROPERTY(VisibleAnywhere, Category = "Trigger Light")
	UPointLightComponent* CubeLight;
};