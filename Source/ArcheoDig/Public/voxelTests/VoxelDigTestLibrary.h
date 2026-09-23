#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "VoxelDigTestLibrary.generated.h"


class UCurveFloat;


/*
 * Учебная библиотека voxel digging experiments.
 *
 * Это не Actor и не Component.
 * Каждая BlueprintCallable функция становится
 * отдельной Blueprint-нодой.
 */
UCLASS()
class ARCHEODIG_API UVoxelDigTestLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()


public:

	// ==================================================
	// 1. REMOVE SPHERE
	// ==================================================

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Remove Sphere C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TryRemoveSphere(
		UObject* WorldContextObject,
		float TraceDistance = 500.0f,
		float Radius = 20.0f,
		bool bDrawDebug = true
	);


	// ==================================================
	// 2. TRIM SPHERE
	// ==================================================

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Trim Sphere C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TryTrimSphere(
		UObject* WorldContextObject,
		float TraceDistance = 500.0f,
		float Radius = 20.0f,
		float Falloff = 0.35f,
		bool bAdditive = false,
		bool bDrawDebug = true
	);


	// ==================================================
	// 3. SURFACE DIG
	// ==================================================
	//
	// Наш основной текущий кандидат.
	//
	// После обычного Surface Edit можно автоматически
	// искать небольшие disconnected fragments
	// и удалять их.

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Surface Dig C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TrySurfaceDig(
		UObject* WorldContextObject,
		float TraceDistance = 500.0f,
		float Radius = 20.0f,
		float Falloff = 0.55f,
		float Strength = 10.0f,

		// Включить автоматическую очистку
		// маленьких оторванных кусков.
		bool bCleanupFloatingFragments = true,

		// Радиус области, которую проверяем
		// после каждого копка.
		float CleanupRadius = 100.0f,

		// Максимальный размер отдельного куска
		// в количестве voxel samples.
		//
		// Если кусок больше этого значения,
		// первая версия cleanup его оставит.
		int32 MaxFragmentVoxels = 100,

		bool bDrawDebug = true
	);


	// ==================================================
	// 4. SURFACE + FLATTEN
	// ==================================================

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Surface Flatten C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TrySurfaceFlatten(
		UObject* WorldContextObject,
		float TraceDistance = 500.0f,
		float Radius = 20.0f,
		float Falloff = 0.55f,
		float Strength = 10.0f,
		bool bDrawDebug = true
	);


	// ==================================================
	// 5. SURFACE + STRENGTH CURVE
	// ==================================================

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Surface Strength Curve C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TrySurfaceStrengthCurve(
		UObject* WorldContextObject,
		UCurveFloat* StrengthCurve,
		float TraceDistance = 500.0f,
		float Radius = 20.0f,
		float Strength = 10.0f,
		bool bDrawDebug = true
	);


	// ==================================================
	// 6. SURFACE + STRENGTH MASK
	// ==================================================

	UFUNCTION(
		BlueprintCallable,
		Category = "ArcheoDig|Voxel Tests",
		meta = (
			DisplayName = "Try Surface Strength Mask C++",
			WorldContext = "WorldContextObject"
			)
	)
	static bool TrySurfaceStrengthMask(
		UObject* WorldContextObject
	);
};