#include "voxelTests/VoxelDigTestLibrary.h"


// ======================================================
// UNREAL
// ======================================================

#include "Engine/Engine.h"
#include "Engine/World.h"

#include "Kismet/GameplayStatics.h"

#include "Camera/PlayerCameraManager.h"

#include "GameFramework/Pawn.h"

#include "DrawDebugHelpers.h"

#include "Curves/CurveFloat.h"


// ======================================================
// VOXEL PLUGIN FREE LEGACY
// ======================================================

#include "VoxelWorld.h"

#include "VoxelTools/Gen/VoxelSphereTools.h"

#include "VoxelTools/VoxelBlueprintLibrary.h"

#include "VoxelTools/VoxelSurfaceTools.h"

#include "VoxelTools/Gen/VoxelSurfaceEditTools.h"


// Для прямого чтения/записи voxel data.
#include "VoxelData/VoxelData.h"

// ВАЖНО:
// здесь находятся реализации template-функций FVoxelData,
// в том числе Set<FVoxelValue>().
#include "VoxelData/VoxelData.inl"

// Для одного безопасного lock на всю cleanup-операцию.
#include "VoxelData/VoxelDataLock.h"

// FVoxelValue::Empty()
#include "VoxelValue.h"


// ======================================================
// ВНУТРЕННИЕ ФУНКЦИИ
// ======================================================
//
// Они существуют только внутри этого .cpp.
// Blueprint их не видит.
// ======================================================

namespace
{

	// ==================================================
	// TRACE RESULT
	// ==================================================

	struct FVoxelDigTraceResult
	{
		UWorld* World = nullptr;

		AVoxelWorld* VoxelWorld = nullptr;

		FVector TraceStart = FVector::ZeroVector;

		FVector TraceEnd = FVector::ZeroVector;

		FVector ImpactPoint = FVector::ZeroVector;

		FVector ImpactNormal = FVector::ZeroVector;
	};


	// ==================================================
	// ОБЩИЙ LINE TRACE
	// ==================================================

	bool TraceVoxelWorld(
		UObject* WorldContextObject,
		float TraceDistance,
		bool bDrawDebug,
		FVoxelDigTraceResult& OutResult
	)
	{
		if (!IsValid(WorldContextObject))
		{
			return false;
		}


		if (!GEngine)
		{
			return false;
		}


		UWorld* World =
			GEngine->GetWorldFromContextObject(
				WorldContextObject,
				EGetWorldErrorMode::ReturnNull
			);


		if (!World)
		{
			return false;
		}


		APlayerCameraManager* CameraManager =
			UGameplayStatics::GetPlayerCameraManager(
				WorldContextObject,
				0
			);


		if (!IsValid(CameraManager))
		{
			return false;
		}


		const FVector TraceStart =
			CameraManager->GetCameraLocation();


		const FVector ForwardVector =
			CameraManager
			->GetCameraRotation()
			.Vector();


		const FVector TraceEnd =
			TraceStart
			+ ForwardVector * TraceDistance;


		FCollisionQueryParams QueryParams;


		APawn* PlayerPawn =
			UGameplayStatics::GetPlayerPawn(
				WorldContextObject,
				0
			);


		if (IsValid(PlayerPawn))
		{
			QueryParams.AddIgnoredActor(
				PlayerPawn
			);
		}


		FHitResult HitResult;


		const bool bHit =
			World->LineTraceSingleByChannel(
				HitResult,
				TraceStart,
				TraceEnd,
				ECC_Visibility,
				QueryParams
			);


		if (!bHit)
		{
			if (bDrawDebug)
			{
				DrawDebugLine(
					World,
					TraceStart,
					TraceEnd,
					FColor::Red,
					false,
					0.15f,
					0,
					1.0f
				);
			}


			return false;
		}


		AVoxelWorld* VoxelWorld =
			Cast<AVoxelWorld>(
				HitResult.GetActor()
			);


		if (!IsValid(VoxelWorld))
		{
			return false;
		}


		if (bDrawDebug)
		{
			DrawDebugLine(
				World,
				TraceStart,
				HitResult.ImpactPoint,
				FColor::Green,
				false,
				0.15f,
				0,
				1.0f
			);


			DrawDebugPoint(
				World,
				HitResult.ImpactPoint,
				12.0f,
				FColor::Yellow,
				false,
				0.15f
			);
		}


		OutResult.World =
			World;

		OutResult.VoxelWorld =
			VoxelWorld;

		OutResult.TraceStart =
			TraceStart;

		OutResult.TraceEnd =
			TraceEnd;

		OutResult.ImpactPoint =
			HitResult.ImpactPoint;

		OutResult.ImpactNormal =
			HitResult.ImpactNormal;


		return true;
	}


	// ==================================================
	// FIND SURFACE VOXELS
	// ==================================================

	bool FindSurfaceVoxels(
		const FVoxelDigTraceResult& Trace,
		float Radius,
		FVoxelSurfaceEditsVoxels& OutSurfaceVoxels
	)
	{
		if (!IsValid(Trace.VoxelWorld))
		{
			return false;
		}


		const FVoxelIntBox Bounds =
			UVoxelBlueprintLibrary
			::MakeIntBoxFromGlobalPositionAndRadius(
				Trace.VoxelWorld,
				Trace.ImpactPoint,
				Radius
			);


		if (!Bounds.IsValid())
		{
			return false;
		}


		UVoxelSurfaceTools
			::FindSurfaceVoxelsFromDistanceField(
				OutSurfaceVoxels,
				Trace.VoxelWorld,
				Bounds,
				false
			);


		return true;
	}


	// ==================================================
	// EDIT SURFACE VOXELS
	// ==================================================

	void EditSurfaceVoxels(
		AVoxelWorld* VoxelWorld,
		const FVoxelSurfaceEditsProcessedVoxels& ProcessedVoxels
	)
	{
		UVoxelSurfaceEditTools::EditVoxelValues(
			VoxelWorld,
			ProcessedVoxels,

			// Distance Divisor
			1.0f,

			// Modified Values
			nullptr,

			// Edited Bounds
			nullptr,

			// Multi Threaded
			true,

			// Update Render
			true
		);
	}


	// ==================================================
	// FLOATING FRAGMENTS CLEANUP
	// ==================================================
	//
	// Идея:
	//
	// берём локальный куб вокруг ImpactPoint
	//
	// читаем все density values за один раз
	//
	// ищем connected components среди solid voxels
	//
	// если component:
	//
	//   1. НЕ касается края нашего локального Bounds
	//   2. маленький
	//
	// считаем его локальным оторванным островком
	// и превращаем все его voxels в Empty.
	//
	//
	// Сейчас используется 6-connected flood fill:
	//
	// +X
	// -X
	// +Y
	// -Y
	// +Z
	// -Z
	//
	// Диагонали пока соединением не считаются.
	// ==================================================

	int32 CleanupFloatingFragments(
		AVoxelWorld* VoxelWorld,
		const FVector& WorldCenter,
		float CleanupRadius,
		int32 MaxFragmentVoxels,
		bool bDrawDebug
	)
	{
		// ----------------------------------------------
		// Базовые проверки
		// ----------------------------------------------

		if (!IsValid(VoxelWorld))
		{
			return 0;
		}


		if (!VoxelWorld->IsCreated())
		{
			return 0;
		}


		if (CleanupRadius <= 0.0f)
		{
			return 0;
		}


		if (MaxFragmentVoxels <= 0)
		{
			return 0;
		}


		// ----------------------------------------------
		// Создаём локальную область проверки
		// ----------------------------------------------

		const FVoxelIntBox Bounds =
			UVoxelBlueprintLibrary
			::MakeIntBoxFromGlobalPositionAndRadius(
				VoxelWorld,
				WorldCenter,
				CleanupRadius
			);


		if (!Bounds.IsValid())
		{
			return 0;
		}


		const FIntVector Size =
			Bounds.Size();


		if (
			Size.X <= 0 ||
			Size.Y <= 0 ||
			Size.Z <= 0
			)
		{
			return 0;
		}


		// ----------------------------------------------
		// Количество ячеек в локальном массиве
		// ----------------------------------------------

		const int32 TotalVoxelCount =
			Size.X
			* Size.Y
			* Size.Z;


		if (TotalVoxelCount <= 0)
		{
			return 0;
		}


		// ----------------------------------------------
		// Вспомогательная функция:
		//
		// X Y Z -> индекс одномерного массива
		//
		// Это та же схема хранения,
		// которую использует Voxel Plugin.
		// ----------------------------------------------

		const auto ToIndex =
			[&Size](
				int32 X,
				int32 Y,
				int32 Z
				)
			{
				return
					X
					+ Y * Size.X
					+ Z * Size.X * Size.Y;
			};


		// ----------------------------------------------
		// Обратное преобразование:
		//
		// индекс -> X Y Z
		// ----------------------------------------------

		const auto FromIndex =
			[&Size](
				int32 Index
				)
			{
				const int32 PlaneSize =
					Size.X * Size.Y;


				const int32 Z =
					Index / PlaneSize;


				const int32 Remaining =
					Index - Z * PlaneSize;


				const int32 Y =
					Remaining / Size.X;


				const int32 X =
					Remaining - Y * Size.X;


				return FIntVector(
					X,
					Y,
					Z
				);
			};


		// ----------------------------------------------
		// Эти voxels в итоге будем удалять.
		// ----------------------------------------------

		TArray<int32> VoxelsToRemove;


		// Сколько отдельных fragments нашли.
		int32 RemovedFragments = 0;


		// ==================================================
		// LOCK
		// ==================================================
		//
		// Очень важная часть.
		//
		// Мы НЕ вызываем GetValue для каждого voxel
		// отдельной Blueprint/C++ функцией.
		//
		// Один раз блокируем небольшой Bounds,
		// читаем весь блок,
		// анализируем его в памяти,
		// потом записываем изменения.
		// ==================================================

		{
			FVoxelData& Data =
				VoxelWorld->GetData();


			FVoxelWriteScopeLock Lock(
				Data,
				Bounds,
				FName(TEXT("CleanupFloatingFragments"))
			);


			// ------------------------------------------
			// Читаем весь маленький voxel block
			// одним вызовом.
			// ------------------------------------------

			const TArray<FVoxelValue> Values =
				Data.GetValues(
					Bounds
				);


			if (Values.Num() != TotalVoxelCount)
			{
				return 0;
			}


			// ------------------------------------------
			// Уже посещённые voxels.
			//
			// 0 = ещё не были
			// 1 = уже были
			// ------------------------------------------

			TArray<uint8> Visited;

			Visited.Init(
				0,
				TotalVoxelCount
			);


			// ------------------------------------------
			// 6 соседей voxel.
			// ------------------------------------------

			static const FIntVector NeighborOffsets[] =
			{
				FIntVector(1,  0,  0),
				FIntVector(-1,  0,  0),

				FIntVector(0,  1,  0),
				FIntVector(0, -1,  0),

				FIntVector(0,  0,  1),
				FIntVector(0,  0, -1)
			};


			// ==================================================
			// ПРОХОДИМ ПО ВСЕМ VOXELS
			// ==================================================

			for (
				int32 StartIndex = 0;
				StartIndex < TotalVoxelCount;
				StartIndex++
				)
			{
				// Уже обработан.
				if (Visited[StartIndex])
				{
					continue;
				}


				// Помечаем сразу,
				// чтобы не возвращаться сюда.
				Visited[StartIndex] = 1;


				const FVoxelValue StartValue =
					Values[StartIndex];


				// Пустой voxel нас не интересует.
				//
				// Solid:
				// Value <= 0
				//
				// Empty:
				// Value > 0
				if (StartValue.IsEmpty())
				{
					continue;
				}


				// ==========================================
				// НАШЛИ НОВЫЙ SOLID COMPONENT
				// ==========================================

				TArray<int32> Queue;

				TArray<int32> Component;


				Queue.Add(
					StartIndex
				);


				Component.Add(
					StartIndex
				);


				int32 QueueHead = 0;


				// Если component касается края Bounds,
				// считаем его частью большой земли.
				bool bTouchesBoundary = false;


				// ==========================================
				// FLOOD FILL
				// ==========================================

				while (
					QueueHead < Queue.Num()
					)
				{
					const int32 CurrentIndex =
						Queue[QueueHead];


					QueueHead++;


					const FIntVector LocalPosition =
						FromIndex(
							CurrentIndex
						);


					// --------------------------------------
					// Проверяем:
					// дошёл ли component до края Bounds.
					// --------------------------------------

					if (
						LocalPosition.X == 0 ||
						LocalPosition.Y == 0 ||
						LocalPosition.Z == 0 ||

						LocalPosition.X == Size.X - 1 ||
						LocalPosition.Y == Size.Y - 1 ||
						LocalPosition.Z == Size.Z - 1
						)
					{
						bTouchesBoundary = true;
					}


					// --------------------------------------
					// Проверяем 6 соседей.
					// --------------------------------------

					for (
						const FIntVector& Offset
						: NeighborOffsets
						)
					{
						const FIntVector Neighbor =
							LocalPosition + Offset;


						// Вышли за наш локальный Bounds.
						if (
							Neighbor.X < 0 ||
							Neighbor.Y < 0 ||
							Neighbor.Z < 0 ||

							Neighbor.X >= Size.X ||
							Neighbor.Y >= Size.Y ||
							Neighbor.Z >= Size.Z
							)
						{
							continue;
						}


						const int32 NeighborIndex =
							ToIndex(
								Neighbor.X,
								Neighbor.Y,
								Neighbor.Z
							);


						if (Visited[NeighborIndex])
						{
							continue;
						}


						Visited[NeighborIndex] = 1;


						const FVoxelValue NeighborValue =
							Values[NeighborIndex];


						// Воздух не входит
						// в solid component.
						if (NeighborValue.IsEmpty())
						{
							continue;
						}


						Queue.Add(
							NeighborIndex
						);


						Component.Add(
							NeighborIndex
						);
					}
				}


				// ==================================================
				// РЕШАЕМ:
				// УДАЛЯТЬ COMPONENT ИЛИ НЕТ
				// ==================================================
				//
				// Если component касается края локальной области,
				// мы НЕ можем доказать, что он floating.
				//
				// Возможно, он продолжается за Bounds
				// и является основной землёй.
				//
				// Поэтому оставляем.
				// ==================================================

				if (bTouchesBoundary)
				{
					continue;
				}


				// Слишком большой fragment.
				//
				// Первая версия cleanup специально
				// консервативная.
				if (
					Component.Num()
							> MaxFragmentVoxels
					)
				{
					continue;
				}


				// ------------------------------------------
				// Это маленький isolated component.
				// Запоминаем для удаления.
				// ------------------------------------------

				VoxelsToRemove.Append(
					Component
				);


				RemovedFragments++;
			}


			// ==================================================
			// УДАЛЯЕМ НАЙДЕННЫЕ VOXELS
			// ==================================================

			for (
				const int32 Index
				: VoxelsToRemove
				)
			{
				const FIntVector LocalPosition =
					FromIndex(
						Index
					);


				const FIntVector VoxelPosition =
					Bounds.Min
					+ LocalPosition;


				Data.SetValue(
					VoxelPosition,
					FVoxelValue::Empty()
				);
			}
		}


		// ==================================================
		// LOCK УЖЕ СНЯТ
		// ==================================================
		//
		// После изменения density нужно попросить
		// Voxel Plugin перестроить затронутые chunks.
		// ==================================================

		if (VoxelsToRemove.Num() > 0)
		{
			UVoxelBlueprintLibrary::UpdateBounds(
				VoxelWorld,
				Bounds
			);
		}


		// ==================================================
		// DEBUG
		// ==================================================

		if (
			bDrawDebug &&
			VoxelsToRemove.Num() > 0 &&
			GEngine
			)
		{
			const FString Message =
				FString::Printf(
					TEXT(
						"Cleanup: fragments %d | voxels %d"
					),
					RemovedFragments,
					VoxelsToRemove.Num()
				);


			GEngine->AddOnScreenDebugMessage(
				2001,
				1.5f,
				FColor::Orange,
				Message
			);
		}


		return VoxelsToRemove.Num();
	}
}


// ======================================================
// 1. REMOVE SPHERE
// ======================================================

bool UVoxelDigTestLibrary::TryRemoveSphere(
	UObject* WorldContextObject,
	float TraceDistance,
	float Radius,
	bool bDrawDebug
)
{
	FVoxelDigTraceResult Trace;


	if (!TraceVoxelWorld(
		WorldContextObject,
		TraceDistance,
		bDrawDebug,
		Trace
	))
	{
		return false;
	}


	UVoxelSphereTools::RemoveSphere(
		Trace.VoxelWorld,
		Trace.ImpactPoint,
		Radius,

		nullptr,
		nullptr,

		true,
		true,
		true
	);


	if (bDrawDebug)
	{
		DrawDebugSphere(
			Trace.World,
			Trace.ImpactPoint,
			Radius,
			16,
			FColor::Green,
			false,
			0.15f,
			0,
			1.0f
		);
	}


	return true;
}


// ======================================================
// 2. TRIM SPHERE
// ======================================================

bool UVoxelDigTestLibrary::TryTrimSphere(
	UObject* WorldContextObject,
	float TraceDistance,
	float Radius,
	float Falloff,
	bool bAdditive,
	bool bDrawDebug
)
{
	FVoxelDigTraceResult Trace;


	if (!TraceVoxelWorld(
		WorldContextObject,
		TraceDistance,
		bDrawDebug,
		Trace
	))
	{
		return false;
	}


	const FVector TrimNormal =
		-Trace.ImpactNormal;


	UVoxelSphereTools::TrimSphere(
		Trace.VoxelWorld,

		Trace.ImpactPoint,

		TrimNormal,

		Radius,

		Falloff,

		bAdditive,

		nullptr,
		nullptr,

		true,
		true,
		true
	);


	if (bDrawDebug)
	{
		DrawDebugSphere(
			Trace.World,
			Trace.ImpactPoint,
			Radius,
			16,
			FColor::Cyan,
			false,
			0.15f,
			0,
			1.0f
		);
	}


	return true;
}


// ======================================================
// 3. SURFACE DIG
// ======================================================

bool UVoxelDigTestLibrary::TrySurfaceDig(
	UObject* WorldContextObject,
	float TraceDistance,
	float Radius,
	float Falloff,
	float Strength,
	bool bCleanupFloatingFragments,
	float CleanupRadius,
	int32 MaxFragmentVoxels,
	bool bDrawDebug
)
{
	FVoxelDigTraceResult Trace;


	if (!TraceVoxelWorld(
		WorldContextObject,
		TraceDistance,
		bDrawDebug,
		Trace
	))
	{
		return false;
	}


	FVoxelSurfaceEditsVoxels SurfaceVoxels;


	if (!FindSurfaceVoxels(
		Trace,
		Radius,
		SurfaceVoxels
	))
	{
		return false;
	}


	FVoxelSurfaceEditsStack Stack;


	// ----------------------------------------------
	// Smooth Falloff
	// ----------------------------------------------

	Stack.Add(
		UVoxelSurfaceTools::ApplyFalloff(
			Trace.VoxelWorld,
			EVoxelFalloff::Smooth,
			Trace.ImpactPoint,
			Radius,
			Falloff,
			true
		)
	);


	// ----------------------------------------------
	// Constant Strength
	// ----------------------------------------------

	Stack.Add(
		UVoxelSurfaceTools::ApplyConstantStrength(
			Strength
		)
	);


	// ----------------------------------------------
	// Apply Stack
	// ----------------------------------------------

	const FVoxelSurfaceEditsProcessedVoxels ProcessedVoxels =
		UVoxelSurfaceTools::ApplyStack(
			SurfaceVoxels,
			Stack
		);


	// ----------------------------------------------
	// Реальное изменение земли
	// ----------------------------------------------

	EditSurfaceVoxels(
		Trace.VoxelWorld,
		ProcessedVoxels
	);


	// ==================================================
	// FLOATING FRAGMENTS CLEANUP
	// ==================================================
	//
	// Surface Dig сначала делает обычную яму.
	//
	// И только ПОСЛЕ этого анализируем
	// локальную область вокруг копка.
	// ==================================================

	if (bCleanupFloatingFragments)
	{
		CleanupFloatingFragments(
			Trace.VoxelWorld,
			Trace.ImpactPoint,
			CleanupRadius,
			MaxFragmentVoxels,
			bDrawDebug
		);
	}


	if (bDrawDebug)
	{
		DrawDebugSphere(
			Trace.World,
			Trace.ImpactPoint,
			Radius,
			16,
			FColor::Green,
			false,
			0.15f,
			0,
			1.0f
		);
	}


	return true;
}


// ======================================================
// 4. SURFACE + FLATTEN
// ======================================================

bool UVoxelDigTestLibrary::TrySurfaceFlatten(
	UObject* WorldContextObject,
	float TraceDistance,
	float Radius,
	float Falloff,
	float Strength,
	bool bDrawDebug
)
{
	FVoxelDigTraceResult Trace;


	if (!TraceVoxelWorld(
		WorldContextObject,
		TraceDistance,
		bDrawDebug,
		Trace
	))
	{
		return false;
	}


	FVoxelSurfaceEditsVoxels SurfaceVoxels;


	if (!FindSurfaceVoxels(
		Trace,
		Radius,
		SurfaceVoxels
	))
	{
		return false;
	}


	FVoxelSurfaceEditsStack Stack;


	Stack.Add(
		UVoxelSurfaceTools::ApplyFalloff(
			Trace.VoxelWorld,
			EVoxelFalloff::Smooth,
			Trace.ImpactPoint,
			Radius,
			Falloff,
			true
		)
	);


	Stack.Add(
		UVoxelSurfaceTools::ApplyConstantStrength(
			Strength
		)
	);


	Stack.Add(
		UVoxelSurfaceTools::ApplyFlatten(
			Trace.VoxelWorld,
			Trace.ImpactPoint,
			Trace.ImpactNormal,
			EVoxelSDFMergeMode::Intersection,
			true
		)
	);


	const FVoxelSurfaceEditsProcessedVoxels ProcessedVoxels =
		UVoxelSurfaceTools::ApplyStack(
			SurfaceVoxels,
			Stack
		);


	EditSurfaceVoxels(
		Trace.VoxelWorld,
		ProcessedVoxels
	);


	if (bDrawDebug)
	{
		DrawDebugSphere(
			Trace.World,
			Trace.ImpactPoint,
			Radius,
			16,
			FColor::Blue,
			false,
			0.15f,
			0,
			1.0f
		);
	}


	return true;
}


// ======================================================
// 5. SURFACE + STRENGTH CURVE
// ======================================================

bool UVoxelDigTestLibrary::TrySurfaceStrengthCurve(
	UObject* WorldContextObject,
	UCurveFloat* StrengthCurve,
	float TraceDistance,
	float Radius,
	float Strength,
	bool bDrawDebug
)
{
	if (!IsValid(StrengthCurve))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(
				-1,
				3.0f,
				FColor::Red,
				TEXT(
					"TrySurfaceStrengthCurve: назначь Curve Float"
				)
			);
		}


		return false;
	}


	FVoxelDigTraceResult Trace;


	if (!TraceVoxelWorld(
		WorldContextObject,
		TraceDistance,
		bDrawDebug,
		Trace
	))
	{
		return false;
	}


	FVoxelSurfaceEditsVoxels SurfaceVoxels;


	if (!FindSurfaceVoxels(
		Trace,
		Radius,
		SurfaceVoxels
	))
	{
		return false;
	}


	FVoxelSurfaceEditsStack Stack;


	Stack.Add(
		UVoxelSurfaceTools::ApplyStrengthCurve(
			Trace.VoxelWorld,
			Trace.ImpactPoint,
			Radius,
			StrengthCurve,
			true
		)
	);


	Stack.Add(
		UVoxelSurfaceTools::ApplyConstantStrength(
			Strength
		)
	);


	const FVoxelSurfaceEditsProcessedVoxels ProcessedVoxels =
		UVoxelSurfaceTools::ApplyStack(
			SurfaceVoxels,
			Stack
		);


	EditSurfaceVoxels(
		Trace.VoxelWorld,
		ProcessedVoxels
	);


	if (bDrawDebug)
	{
		DrawDebugSphere(
			Trace.World,
			Trace.ImpactPoint,
			Radius,
			16,
			FColor::Purple,
			false,
			0.15f,
			0,
			1.0f
		);
	}


	return true;
}


// ======================================================
// 6. SURFACE + STRENGTH MASK
// ======================================================

bool UVoxelDigTestLibrary::TrySurfaceStrengthMask(
	UObject* WorldContextObject
)
{
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(
			-1,
			4.0f,
			FColor::Red,
			TEXT(
				"Surface Strength Mask недоступен: "
				"Voxel Plugin Free Legacy требует Pro"
			)
		);
	}


	return false;
}