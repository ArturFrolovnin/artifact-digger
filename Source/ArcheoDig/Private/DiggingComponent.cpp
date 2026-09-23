#include "DiggingComponent.h"

// Игровой World и время.
#include "Engine/World.h"

// Debug text.
#include "Engine/Engine.h"

// Debug Line / Point.
#include "DrawDebugHelpers.h"

// Player Controller.
#include "GameFramework/PlayerController.h"

// Pawn игрока.
#include "GameFramework/Pawn.h"

// Camera Manager.
#include "Camera/PlayerCameraManager.h"

// GetPlayerController / GetPlayerCameraManager.
#include "Kismet/GameplayStatics.h"

// Left Mouse Button / EKeys.
#include "InputCoreTypes.h"

// Наш SoilBlocks — Instanced Static Mesh Component.
#include "Components/InstancedStaticMeshComponent.h"


UDiggingComponent::UDiggingComponent()
{
	// У DiggingComponent нет собственного Tick.
	//
	// Пока scheduling остаётся в Blueprint:
	//
	// Event Tick
	//      ↓
	// ProcessDigging()
	//
	// Позже можем заменить это на Timer
	// или собственный TickComponent.
	PrimaryComponentTick.bCanEverTick = false;
}


void UDiggingComponent::ProcessDigging()
{
	// ==================================================
	// 1. Получаем World
	// ==================================================

	UWorld* World = GetWorld();

	if (!World)
	{
		return;
	}


	// ==================================================
	// 2. Получаем Player Controller
	// ==================================================
	//
	// Blueprint аналог:
	//
	// Get Player Controller
	//      ↓
	// Is Valid
	//

	APlayerController* PlayerController =
		UGameplayStatics::GetPlayerController(this, 0);

	if (!IsValid(PlayerController))
	{
		return;
	}


	// ==================================================
	// 3. Получаем Pawn игрока
	// ==================================================
	//
	// Blueprint:
	//
	// Get Player Pawn
	//      ↓
	// Is Valid
	//

	APawn* PlayerPawn = PlayerController->GetPawn();

	if (!IsValid(PlayerPawn))
	{
		return;
	}


	// ==================================================
	// 4. Проверяем ЛКМ
	// ==================================================
	//
	// Старый Blueprint:
	//
	// Is Input Key Down
	//          OR
	// Was Input Key Just Pressed
	//          ↓
	//        Branch
	//

	const bool bMouseHeld =
		PlayerController->IsInputKeyDown(EKeys::LeftMouseButton);

	const bool bMouseJustPressed =
		PlayerController->WasInputKeyJustPressed(EKeys::LeftMouseButton);


	// Если мышь не нажата —
	// дальше вообще ничего не делаем.
	if (!bMouseHeld && !bMouseJustPressed)
	{
		return;
	}


	// ==================================================
	// 5. DigInterval
	// ==================================================

	const float CurrentTime = World->GetTimeSeconds();


	// Например:
	//
	// CurrentTime = 5.10
	// NextDigTime = 5.25
	//
	// Значит копать ещё рано.
	if (CurrentTime < NextDigTime)
	{
		return;
	}


	// Разрешаем следующий копок
	// только через DigInterval секунд.
	//
	// Старый Blueprint:
	//
	// NextDigTime =
	// Get Game Time In Seconds + DigInterval
	//
	NextDigTime =
		CurrentTime + FMath::Max(DigInterval, 0.0f);


	// ==================================================
	// 6. Получаем Camera Manager
	// ==================================================
	//
	// Blueprint:
	//
	// Get Player Camera Manager
	//

	APlayerCameraManager* CameraManager =
		UGameplayStatics::GetPlayerCameraManager(this, 0);

	if (!IsValid(CameraManager))
	{
		return;
	}


	// ==================================================
	// 7. Camera Location
	// ==================================================

	const FVector CameraLocation =
		CameraManager->GetCameraLocation();


	// ==================================================
	// 8. Camera Rotation
	// ==================================================

	const FRotator CameraRotation =
		CameraManager->GetCameraRotation();


	// ==================================================
	// 9. Forward Vector
	// ==================================================
	//
	// Blueprint:
	//
	// Get Camera Rotation
	//      ↓
	// Get Forward Vector
	//

	const FVector ForwardVector =
		CameraRotation.Vector();


	// ==================================================
	// 10. Создаём Start / End Line Trace
	// ==================================================

	const FVector TraceStart =
		CameraLocation;


	const FVector TraceEnd =
		TraceStart + ForwardVector * TraceDistance;


	// ==================================================
	// 11. Настраиваем Line Trace
	// ==================================================

	FHitResult HitResult;

	FCollisionQueryParams QueryParams;


	// Не позволяем лучу попасть
	// в собственного персонажа.
	//
	// Blueprint аналог:
	//
	// Get Player Pawn
	//      ↓
	// Make Array
	//      ↓
	// Actors To Ignore
	//
	QueryParams.AddIgnoredActor(PlayerPawn);


	// ВАЖНО:
	//
	// BP_DiggableGround специально НЕ игнорируем.
	//
	// Нам как раз нужно попасть лучом
	// в SoilBlocks этого Actor.


	// ==================================================
	// 12. Line Trace By Channel
	// ==================================================
	//
	// Blueprint:
	//
	// Line Trace By Channel
	//
	// Start         = TraceStart
	// End           = TraceEnd
	// Trace Channel = Visibility
	//

	const bool bHit =
		World->LineTraceSingleByChannel(
			HitResult,
			TraceStart,
			TraceEnd,
			ECC_Visibility,
			QueryParams
		);


	// ==================================================
	// 13. Debug Line
	// ==================================================

	if (bDrawDebug)
	{
		if (bHit)
		{
			// Попали:
			// зелёная линия до Impact Point.
			DrawDebugLine(
				World,
				TraceStart,
				HitResult.ImpactPoint,
				FColor::Green,
				false,
				DigInterval,
				0,
				1.0f
			);


			// Жёлтая точка попадания.
			DrawDebugPoint(
				World,
				HitResult.ImpactPoint,
				12.0f,
				FColor::Yellow,
				false,
				DigInterval
			);
		}
		else
		{
			// Не попали:
			// красная линия на полную длину trace.
			DrawDebugLine(
				World,
				TraceStart,
				TraceEnd,
				FColor::Red,
				false,
				DigInterval,
				0,
				1.0f
			);
		}
	}


	// Если Line Trace ничего не нашёл —
	// копать нечего.
	if (!bHit)
	{
		return;
	}


	// ==================================================
	// 14. Получаем Actor земли
	// ==================================================

	AActor* GroundActor = GetOwner();

	if (!IsValid(GroundActor))
	{
		return;
	}


	// ==================================================
	// 15. Получаем SoilBlocks
	// ==================================================
	//
	// В текущем BP_DiggableGround находится
	// один Instanced Static Mesh Component:
	//
	// SoilBlocks
	//
	// Поэтому можем получить его по типу.
	//

	UInstancedStaticMeshComponent* SoilBlocks =
		GroundActor->FindComponentByClass<UInstancedStaticMeshComponent>();

	if (!IsValid(SoilBlocks))
	{
		return;
	}


	// ==================================================
	// 16. Проверяем, что луч попал именно в SoilBlocks
	// ==================================================
	//
	// Blueprint аналог:
	//
	// Hit Component
	//      ==
	// SoilBlocks
	//

	if (HitResult.GetComponent() != SoilBlocks)
	{
		return;
	}


	// ==================================================
	// 17. Проверяем DigReach
	// ==================================================
	//
	// ВАЖНО:
	//
	// Line Trace имеет длину 800 см,
	// но копать мы разрешаем только на 350 см.
	//
	// И расстояние считаем именно
	// ОТ ПЕРСОНАЖА,
	// а не от камеры.
	//

	const float DistanceToHit =
		FVector::Distance(
			PlayerPawn->GetActorLocation(),
			HitResult.ImpactPoint
		);


	if (DistanceToHit > DigReach)
	{
		return;
	}


	// ==================================================
	// 18. Ищем voxel вокруг точки попадания
	// ==================================================
	//
	// Blueprint:
	//
	// Get Instances Overlapping Sphere
	//
	// Center = Impact Point
	// Radius = DigRadius
	// Sphere In World Space = true
	//

	const TArray<int32> InstanceIndices =
		SoilBlocks->GetInstancesOverlappingSphere(
			HitResult.ImpactPoint,
			DigRadius,
			true
		);


	// Если ни одного voxel не нашли —
	// больше ничего делать не нужно.
	if (InstanceIndices.Num() == 0)
	{
		return;
	}


	// ==================================================
	// 19. Удаляем найденные voxel
	// ==================================================
	//
	// ВАЖНО:
	//
	// Используем ОДИН RemoveInstances.
	//
	// Не делаем:
	//
	// for (...)
	//     RemoveInstance(...)
	//
	// потому что при удалении одного элемента
	// индексы остальных могут сдвигаться.
	//
	// RemoveInstances умеет корректно обработать
	// массив индексов целиком.
	//

	SoilBlocks->RemoveInstances(InstanceIndices);


	// ==================================================
	// 20. Debug информация
	// ==================================================

	if (GEngine)
	{
		const FString Message =
			FString::Printf(
				TEXT("Удалено voxel: %d | Distance: %.0f cm"),
				InstanceIndices.Num(),
				DistanceToHit
			);

		GEngine->AddOnScreenDebugMessage(
			1002,
			1.0f,
			FColor::Yellow,
			Message
		);
	}
}