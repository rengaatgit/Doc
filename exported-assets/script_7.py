# Create LangGraph orchestrator for agent coordination

langgraph_orchestrator_code = '''
"""
LangGraph Orchestrator for LC Validation
Coordinates multiple validation agents in parallel using LangGraph
"""

import asyncio
from typing import Dict, List, Any, Optional
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from dataclasses import dataclass, field
import json
from datetime import datetime

from ..agents.credit_type_agent import CreditTypeAgent
from ..agents.date_validation_agent import DateValidationAgent  
from ..agents.amount_validation_agent import AmountValidationAgent
from ..agents.document_requirements_agent import DocumentRequirementsAgent
from ..agents.shipping_terms_agent import ShippingTermsAgent
from ..agents.bank_details_agent import BankDetailsAgent
from ..parsers.lc_parser import LCData


@dataclass
class ValidationState:
    """State object for LangGraph validation workflow"""
    lc_data: LCData
    validation_results: Dict[str, Any] = field(default_factory=dict)
    completed_agents: List[str] = field(default_factory=list)
    failed_agents: List[str] = field(default_factory=list)
    overall_status: str = "pending"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    final_report: Dict[str, Any] = field(default_factory=dict)


class LCValidationOrchestrator:
    """Main orchestrator for LC validation using LangGraph"""
    
    def __init__(self, config: Dict, vector_db_manager):
        self.config = config
        self.vector_db = vector_db_manager
        
        # Initialize validation agents
        self.agents = {
            "credit_type": CreditTypeAgent(config, vector_db_manager),
            "date_validation": DateValidationAgent(config, vector_db_manager),
            "amount_validation": AmountValidationAgent(config, vector_db_manager),
            "document_requirements": DocumentRequirementsAgent(config, vector_db_manager),
            "shipping_terms": ShippingTermsAgent(config, vector_db_manager),
            "bank_details": BankDetailsAgent(config, vector_db_manager)
        }
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for validation"""
        workflow = StateGraph(ValidationState)
        
        # Add nodes for each validation agent
        for agent_name in self.agents.keys():
            workflow.add_node(agent_name, self._create_agent_node(agent_name))
        
        # Add aggregation and reporting nodes
        workflow.add_node("aggregate_results", self._aggregate_results)
        workflow.add_node("generate_report", self._generate_final_report)
        
        # Define the workflow edges
        workflow.set_entry_point("credit_type")
        
        # All agents can run in parallel after credit_type validation
        for agent_name in ["date_validation", "amount_validation", "document_requirements", 
                          "shipping_terms", "bank_details"]:
            workflow.add_edge("credit_type", agent_name)
            workflow.add_edge(agent_name, "aggregate_results")
        
        workflow.add_edge("aggregate_results", "generate_report")
        workflow.set_finish_point("generate_report")
        
        return workflow.compile()
    
    def _create_agent_node(self, agent_name: str):
        """Create a node function for a specific agent"""
        async def agent_node(state: ValidationState) -> ValidationState:
            try:
                agent = self.agents[agent_name]
                result = await agent.validate(state.lc_data)
                
                state.validation_results[agent_name] = result
                state.completed_agents.append(agent_name)
                
                print(f"✓ {agent_name} validation completed")
                
            except Exception as e:
                error_result = {
                    "agent": agent_name,
                    "status": "error",
                    "error": str(e),
                    "validation_result": None
                }
                state.validation_results[agent_name] = error_result
                state.failed_agents.append(agent_name)
                
                print(f"✗ {agent_name} validation failed: {str(e)}")
            
            return state
        
        return agent_node
    
    def _aggregate_results(self, state: ValidationState) -> ValidationState:
        """Aggregate validation results from all agents"""
        print("\\n📊 Aggregating validation results...")
        
        total_agents = len(self.agents)
        completed = len(state.completed_agents)
        failed = len(state.failed_agents)
        
        # Calculate overall compliance
        compliant_count = 0
        total_confidence = 0.0
        
        for agent_name, result in state.validation_results.items():
            if result.get("status") == "completed":
                validation_result = result.get("validation_result", {})
                if validation_result.get("compliant", False):
                    compliant_count += 1
                total_confidence += validation_result.get("confidence", 0.0)
        
        overall_compliance = compliant_count / max(completed, 1)
        average_confidence = total_confidence / max(completed, 1)
        
        state.overall_status = "completed"
        state.end_time = datetime.now()
        
        print(f"Agents completed: {completed}/{total_agents}")
        print(f"Overall compliance: {overall_compliance:.2%}")
        print(f"Average confidence: {average_confidence:.2f}")
        
        return state
    
    def _generate_final_report(self, state: ValidationState) -> ValidationState:
        """Generate final validation report"""
        print("\\n📋 Generating final validation report...")
        
        execution_time = (state.end_time - state.start_time).total_seconds()
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        agent_summaries = {}
        
        for agent_name, result in state.validation_results.items():
            if result.get("status") == "completed":
                validation_result = result.get("validation_result", {})
                agent_summaries[agent_name] = {
                    "compliant": validation_result.get("compliant", False),
                    "confidence": validation_result.get("confidence", 0.0),
                    "issues_count": len(validation_result.get("issues", [])),
                    "recommendations_count": len(validation_result.get("recommendations", []))
                }
                
                all_issues.extend(validation_result.get("issues", []))
                all_recommendations.extend(validation_result.get("recommendations", []))
        
        # Generate final report
        state.final_report = {
            "lc_number": state.lc_data.lc_number,
            "validation_timestamp": state.start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "overall_status": state.overall_status,
            "agents_summary": agent_summaries,
            "total_issues": len(all_issues),
            "total_recommendations": len(all_recommendations),
            "detailed_results": state.validation_results,
            "compliance_summary": {
                "compliant_agents": sum(1 for s in agent_summaries.values() if s["compliant"]),
                "total_agents": len(agent_summaries),
                "overall_compliant": len(all_issues) == 0,
                "confidence_score": sum(s["confidence"] for s in agent_summaries.values()) / len(agent_summaries) if agent_summaries else 0.0
            }
        }
        
        print("✅ Final validation report generated")
        return state
    
    async def validate_lc(self, lc_data: LCData) -> Dict[str, Any]:
        """Main method to validate LC using the LangGraph workflow"""
        print(f"\\n🚀 Starting LC validation for: {lc_data.lc_number}")
        
        # Initialize state
        initial_state = ValidationState(lc_data=lc_data)
        
        # Execute the workflow
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            return final_state.final_report
        except Exception as e:
            print(f"❌ Workflow execution failed: {str(e)}")
            return {
                "lc_number": lc_data.lc_number,
                "status": "failed",
                "error": str(e),
                "validation_timestamp": datetime.now().isoformat()
            }
    
    def get_workflow_graph(self) -> str:
        """Get a string representation of the workflow graph"""
        return """
        LC Validation Workflow:
        
        START → credit_type → [parallel execution]
                              ↓
                 ┌─────────────────────────────┐
                 ▼             ▼             ▼
        date_validation  amount_validation  document_requirements
                 ▼             ▼             ▼
        shipping_terms   bank_details   [other_agents]
                 ▼             ▼             ▼
                 └─────────────┬─────────────┘
                              ▼
                      aggregate_results
                              ▼
                      generate_report
                              ▼
                            END
        """
'''

# Save the LangGraph orchestrator
with open('lc_validation_system/src/orchestrator.py', 'w') as f:
    f.write(langgraph_orchestrator_code)

print("LangGraph orchestrator created:")
print("- src/orchestrator.py")