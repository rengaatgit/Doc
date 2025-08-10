
"""
Example Usage of LC Validation System
Demonstrates how to use the system programmatically
"""

import asyncio
import json
from pathlib import Path
from main import LCValidationSystem


async def example_validation():
    """Example of validating an LC"""
    print("🏦 LC Validation System - Example Usage")
    print("=" * 50)

    # Initialize system
    system = LCValidationSystem()

    # Sample LC text (you can replace this with actual LC content)
    sample_lc_text = """
    IRREVOCABLE DOCUMENTARY LETTER OF CREDIT
    Subject to Uniform Customs & Practice for Documentary Credits, ICC Publication No. 600 (UCP 600)

    LC Number: LC2025-EXAMPLE
    Date of Issue: January 15, 2025

    Issuing Bank:
    Example Bank Ltd.
    123 Banking Street
    New York, NY 10001

    Applicant:
    ABC Imports Inc.
    456 Trade Avenue
    Los Angeles, CA 90001

    Beneficiary:
    XYZ Exports S.A.
    789 Commerce Blvd
    London, UK

    Amount: USD 50,000 (Fifty Thousand U.S. Dollars)
    Expiry Date: March 15, 2025

    Available by sight draft drawn on Example Bank Ltd.

    Documents Required:
    - Signed commercial invoice in duplicate
    - Full set of clean on board ocean bills of lading
    - Insurance policy covering all risks

    Partial Shipments: Not Allowed
    Transshipment: Not Allowed
    """

    try:
        # Validate the LC
        print("\n🔍 Validating sample LC...")
        result = await system.validate_lc_text(sample_lc_text)

        # Display results
        system.print_validation_summary(result)

        # Save to file
        output_file = "example_validation_report.json"
        system.save_validation_report(result, output_file)

        # Show detailed agent results
        print("\n📊 Detailed Agent Results:")
        for agent_name, agent_result in result.get("detailed_results", {}).items():
            print(f"\n{agent_name}:")
            validation_result = agent_result.get("validation_result", {})

            issues = validation_result.get("issues", [])
            if issues:
                print("  Issues:")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"    - {issue}")

            recommendations = validation_result.get("recommendations", [])
            if recommendations:
                print("  Recommendations:")
                for rec in recommendations[:2]:  # Show first 2 recommendations
                    print(f"    - {rec}")

        return result

    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return None


async def batch_validation_example():
    """Example of batch validation of multiple LCs"""
    print("\n🔄 Batch Validation Example")
    print("-" * 30)

    system = LCValidationSystem()

    # List of LC files to validate (add your LC files here)
    lc_files = [
        "sampleLC.txt",
        # "another_lc.txt",
        # "more_lcs.txt"
    ]

    results = []
    for lc_file in lc_files:
        if Path(lc_file).exists():
            print(f"\nValidating {lc_file}...")
            result = await system.validate_lc_file(lc_file)
            results.append(result)

            # Quick summary
            compliance = result.get("compliance_summary", {})
            status = "✅ COMPLIANT" if compliance.get("overall_compliant", False) else "❌ NON-COMPLIANT"
            print(f"Result: {status}")

    print(f"\n📈 Batch validation completed. Processed {len(results)} LCs.")
    return results


if __name__ == "__main__":
    # Run example validation
    asyncio.run(example_validation())

    # Uncomment to run batch validation example
    # asyncio.run(batch_validation_example())
