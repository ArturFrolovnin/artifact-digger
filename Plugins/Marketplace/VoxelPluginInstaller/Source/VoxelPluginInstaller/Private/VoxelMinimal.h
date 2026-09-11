// Copyright Voxel Plugin SAS. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Runtime/Launch/Resources/Version.h"

DECLARE_LOG_CATEGORY_EXTERN(LogVoxelInstaller, Log, All);

#define VOXEL_ENGINE_VERSION (ENGINE_MAJOR_VERSION * 100 + ENGINE_MINOR_VERSION)

#if VOXEL_ENGINE_VERSION >= 502
#define UE_502_SWITCH(Before, AfterOrEqual) AfterOrEqual
#define UE_502_ONLY(...) __VA_ARGS__
#else
#define UE_502_SWITCH(Before, AfterOrEqual) Before
#define UE_502_ONLY(...)
#endif

#if VOXEL_ENGINE_VERSION >= 503
#define UE_503_SWITCH(Before, AfterOrEqual) AfterOrEqual
#define UE_503_ONLY(...) __VA_ARGS__
#else
#define UE_503_SWITCH(Before, AfterOrEqual) Before
#define UE_503_ONLY(...)
#endif

#if VOXEL_ENGINE_VERSION >= 504
#define UE_504_SWITCH(Before, AfterOrEqual) AfterOrEqual
#define UE_504_ONLY(...) __VA_ARGS__
#else
#define UE_504_SWITCH(Before, AfterOrEqual) Before
#define UE_504_ONLY(...)
#endif

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

struct FVoxelLambdaCaller
{
	template<typename T>
	FORCEINLINE auto operator+(T&& Lambda) -> decltype(auto)
	{
		return Lambda();
	}
};

#define INLINE_LAMBDA FVoxelLambdaCaller() + [&]()

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

// Usage: DEFINE_PRIVATE_ACCESS(FMyClass, MyProperty) in global scope, then PrivateAccess::MyProperty(MyObject) from anywhere
#define DEFINE_PRIVATE_ACCESS(Class, Property) \
	namespace PrivateAccess \
	{ \
		template<typename> \
		struct TClass_ ## Property; \
		\
		template<> \
		struct TClass_ ## Property<Class> \
		{ \
			template<auto PropertyPtr> \
			struct TProperty_ ## Property \
			{ \
				friend auto& Property(Class& Object) \
				{ \
					return Object.*PropertyPtr; \
				} \
				friend auto& Property(const Class& Object) \
				{ \
					return Object.*PropertyPtr; \
				} \
			}; \
		}; \
		template struct TClass_ ## Property<Class>::TProperty_ ## Property<&Class::Property>; \
		\
		auto& Property(Class& Object); \
		auto& Property(const Class& Object); \
	}

// Usage: DEFINE_PRIVATE_ACCESS_FUNCTION(FMyClass, MyFunction) in global scope, then PrivateAccess::MyFunction(MyObject)(MyArgs) from anywhere
#define DEFINE_PRIVATE_ACCESS_FUNCTION(Class, Function) \
	namespace PrivateAccess \
	{ \
		template<typename> \
		struct TClass_ ## Function; \
		\
		template<> \
		struct TClass_ ## Function<Class> \
		{ \
			template<auto FunctionPtr> \
			struct TFunction_ ## Function \
			{ \
				friend auto Function(Class& Object) \
				{ \
					return [&Object]<typename... ArgTypes>(ArgTypes&&... Args) \
					{ \
						return (Object.*FunctionPtr)(Forward<ArgTypes>(Args)...); \
					}; \
				} \
			}; \
		}; \
		template struct TClass_ ## Function<Class>::TFunction_ ## Function<&Class::Function>; \
		\
		auto Function(Class& Object); \
		auto Function(const Class& Object) \
		{ \
			return Function(const_cast<Class&>(Object)); \
		} \
	}