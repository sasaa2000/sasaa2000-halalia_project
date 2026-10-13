from .certification_report import CertificationReport

from .certification_rules import CertificationRule
from .amazon_certificate import AmazonCertificate

class CertificationEngine:

    def certify(

        self,

        network_report,

        parser_report,

        pipeline_report,

        stress_report

    ):
        rules = []

        rules.append(

            CertificationRule(

                "Amazon Network",

                network_report.success,

                "Network Validation"

            )

        )

        rules.append(

            CertificationRule(

                "Amazon Parser",

                parser_report.failed_products == 0,

                "Parser Validation"

            )

        )

        rules.append(

            CertificationRule(

                "Pipeline",

                pipeline_report.success,

                "Pipeline Validation"

            )

        )

        rules.append(

            CertificationRule(

                "Stress Test",

                stress_report.success,

                "Runtime Stability"

            )

        )

        passed = all(

            rule.passed

            for rule in rules

        )

        certificate = AmazonCertificate(

            provider="Amazon",

            framework_version="1.0",

            runtime_version="1.0",

            parser_version="1.0",

            certified=passed

        )

        report = CertificationReport(

            provider="Amazon",

            version="PV 5.0",

            rules=rules,

            passed=passed

        )

        return (

            report,

            certificate

        )

