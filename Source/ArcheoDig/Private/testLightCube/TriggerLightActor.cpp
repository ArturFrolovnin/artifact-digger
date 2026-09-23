#include "testLightCube/TriggerLightActor.h"

#include "Components/SceneComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"

#include "GameFramework/Pawn.h"


ATriggerLightActor::ATriggerLightActor()
{
	// Нам не нужен Tick.
	//
	// Мы не проверяем каждый кадр,
	// стоит ли игрок на пластине.
	//
	// Unreal сам вызовет BeginOverlap / EndOverlap.
	PrimaryActorTick.bCanEverTick = false;


	// ==================================================
	// 1. ROOT
	// ==================================================

	Root = CreateDefaultSubobject<USceneComponent>(
		TEXT("Root")
	);

	RootComponent = Root;


	// ==================================================
	// 2. ПЛАСТИНА
	// ==================================================

	PlateMesh = CreateDefaultSubobject<UStaticMeshComponent>(
		TEXT("PlateMesh")
	);

	PlateMesh->SetupAttachment(Root);


	// ==================================================
	// 3. TRIGGER BOX
	// ==================================================

	TriggerBox = CreateDefaultSubobject<UBoxComponent>(
		TEXT("TriggerBox")
	);

	TriggerBox->SetupAttachment(Root);


	// Размер TriggerBox.
	//
	// Важно:
	// SetBoxExtent принимает HALF EXTENT.
	//
	// Поэтому:
	//
	// X = 100 -> полный размер 200 см
	// Y = 100 -> полный размер 200 см
	// Z = 30  -> полный размер 60 см
	TriggerBox->SetBoxExtent(
		FVector(
			100.0f,
			100.0f,
			30.0f
		)
	);


	// Trigger не должен физически блокировать игрока.
	//
	// Нам нужны только collision queries / overlap events.
	TriggerBox->SetCollisionEnabled(
		ECollisionEnabled::QueryOnly
	);


	// По умолчанию игнорируем всё.
	TriggerBox->SetCollisionResponseToAllChannels(
		ECR_Ignore
	);


	// Но Pawn должен вызывать Overlap.
	TriggerBox->SetCollisionResponseToChannel(
		ECC_Pawn,
		ECR_Overlap
	);


	// Явно разрешаем генерировать overlap events.
	TriggerBox->SetGenerateOverlapEvents(true);


	// ==================================================
	// 4. КУБ
	// ==================================================

	CubeMesh = CreateDefaultSubobject<UStaticMeshComponent>(
		TEXT("CubeMesh")
	);

	CubeMesh->SetupAttachment(Root);


	// Ставим куб в 3 метрах от пластины.
	CubeMesh->SetRelativeLocation(
		FVector(
			300.0f,
			0.0f,
			50.0f
		)
	);


	// ==================================================
	// 5. LIGHT
	// ==================================================

	CubeLight = CreateDefaultSubobject<UPointLightComponent>(
		TEXT("CubeLight")
	);

	CubeLight->SetupAttachment(CubeMesh);


	// Ставим свет немного над кубом,
	// чтобы сам CubeMesh не закрывал источник света.
	CubeLight->SetRelativeLocation(
		FVector(
			0.0f,
			0.0f,
			100.0f
		)
	);


	CubeLight->SetIntensity(
		5000.0f
	);


	CubeLight->SetAttenuationRadius(
		500.0f
	);


	// При старте игры свет выключен.
	CubeLight->SetVisibility(false);


	// ==================================================
	// 6. ПОДПИСЫВАЕМСЯ НА OVERLAP EVENTS
	// ==================================================

	TriggerBox->OnComponentBeginOverlap.AddDynamic(
		this,
		&ATriggerLightActor::OnTriggerBeginOverlap
	);


	TriggerBox->OnComponentEndOverlap.AddDynamic(
		this,
		&ATriggerLightActor::OnTriggerEndOverlap
	);
}


// ======================================================
// BEGIN OVERLAP
// ======================================================

void ATriggerLightActor::OnTriggerBeginOverlap(
	UPrimitiveComponent* OverlappedComponent,
	AActor* OtherActor,
	UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex,
	bool bFromSweep,
	const FHitResult& SweepResult
)
{
	// Проверяем:
	// тот Actor, который вошёл в TriggerBox,
	// является Pawn?
	//
	// Cast вернёт nullptr,
	// если OtherActor не Pawn.
	APawn* Pawn = Cast<APawn>(
		OtherActor
	);


	if (!Pawn)
	{
		return;
	}


	// Pawn вошёл в TriggerBox.
	// Включаем свет.
	CubeLight->SetVisibility(true);
}


// ======================================================
// END OVERLAP
// ======================================================

void ATriggerLightActor::OnTriggerEndOverlap(
	UPrimitiveComponent* OverlappedComponent,
	AActor* OtherActor,
	UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex
)
{
	APawn* Pawn = Cast<APawn>(
		OtherActor
	);


	if (!Pawn)
	{
		return;
	}


	// Pawn вышел из TriggerBox.
	// Выключаем свет.
	CubeLight->SetVisibility(false);
}