 CBI-V14 CURSOR RULES (MASTER - AGENTIC EDITION)

Last Updated: October 13, 2025  
Status: ACTIVE AND ENFORCED - AGENTIC AI PLATFORM OPTIMIZED

---

 🎯 CORE PRINCIPLES - PLATFORM WEAKNESSES MITIGATION

 PLATFORM WEAKNESS 1: HALLUCINATED PATHS
- ✅ REALITY CHECK: Always verify existence before operations
- ✅ PATH VALIDATION: Use confirmed absolute paths
- ✅ EXISTENCE VERIFICATION: Never assume resources exist without checking
- ❌ PLATFORM TRAP: Creating non-existent resources in code

 PLATFORM WEAKNESS 2: MEMORY DEGRADATION
- ✅ CONTEXT ANCHORS: Reference specific identifiers when possible
- ✅ CHUNKED REVIEWS: Process components in manageable segments
- ✅ SUMMARY RECAPS: Regular state restoration intervals
- ❌ PLATFORM TRAP: Assuming persistent memory across extended interactions

 PLATFORM WEAKNESS 3: OVER-CONFIDENT ASSUMPTIONS
- ✅ DEFENSIVE CODING: Assume failures will occur
- ✅ EXPLICIT ERROR HANDLING: Never assume operations will succeed
- ✅ REALITY CHECKS: Verify resource states before operations
- ❌ PLATFORM TRAP: "This approach should work" without validation

 PLATFORM WEAKNESS 4: CONTEXT DRIFT
- ✅ EXPLICIT SCOPE: State which components are in context for each operation
- ✅ SEQUENTIAL PROCESSING: Complete one component before moving to next
- ✅ CONTEXT MARKERS: Use structured headers for orientation
- ❌ PLATFORM TRAP: Mixing multiple component contexts in single response

---

 🚨 CRITICAL RULES (ZERO TOLERANCE)

 RULE 1: REALITY-BASED OPERATIONS
```
 MANDATORY PRE-CHECKS
verify_project_structure
locate_actual_resources
confirm_reference_documents
```

 RULE 2: DATA STORE REALITY CHECKS
```
 BEFORE ANY DATA OPERATION
verify_data_store_contents
confirm_resource_counts
validate_operation_parameters
```

 RULE 3: NO TRUST IN PLATFORM MEMORY
- ✅ EXPLICIT RECAPS: "Based on recent interactions, current focus is X"
- ✅ CONTEXT REFRESHERS: Restate current component being modified regularly
- ✅ PROGRESS CHECKPOINTS: "Step 3/7 complete: Component integration"
- ❌ PLATFORM TRAP: "As previously discussed" (assumes memory retention)

 RULE 4: DEFENSIVE ASSUMPTIONS
```
 CORRECT - DEFENSIVE
def execute_operation():
    try:
         Assume external calls might fail
        response = external_call(timeout=30)
        validate_response(response)
        if not response_data:
            log_warning("Operation returned empty response")
            return None
        return processed_data
    except Exception as e:
        log_error(f"Operation failed: {e}")
        return None

 WRONG - OPTIMISTIC
def execute_operation():
     Platform might assume this always works
    return external_call().process()
```

 RULE 5: DATA SOURCE PRIORITIZATION
- ✅ PRIMARY SOURCE: Free external data provider (no API key required)
- ✅ BACKUP SOURCE: Alternative provider (strictly secondary)
- ❌ PLATFORM TRAP: Defaulting to paid services without explicit approval
- ❌ COST VIOLATION: Using backup source when primary is available

---

 🔧 PLATFORM-SPECIFIC PATTERNS

 Resource Discovery Pattern
```
 ALWAYS RUN FIRST WHEN UNCERTAIN
locate_project_components
identify_relevant_resources
verify_current_environment
```

 Context Management Pattern
```
=== CONTEXT SETUP ===
Current focus: Specific integration task
Components in context:
- Primary implementation component
- Reference architecture document
- Supporting configuration elements

Let me verify these components exist first:
```

 Memory Reinforcement Pattern
```
=== PROGRESS RECAP ===
Recent interaction sequence:
1. User requested specific functionality
2. We reviewed architecture reference
3. We verified implementation component exists
4. We added error handling to external calls
5. Now implementing data persistence function

Current objective: Complete data persistence with proper error handling
```

 Data Source Selection Protocol
```
=== SOURCE SELECTION PROTOCOL ===
Priority Order:
1. Free external provider (no authentication)
2. Existing cached data (if fresh)
3. Alternative provider (backup only)
4. Manual input (last resort)

Current selection: Primary free provider
Backup available: Yes (secondary provider)
Cost impact: Zero (primary selected)
```

---

 📋 AGENTIC DEVELOPMENT WORKFLOW

 Platform-Optimized Workflow
```
 1. REALITY CHECK - what's actually changed?
check_current_state
identify_modified_components

 2. CONTEXT AWARE COMMITMENTS
review_each_modification  Platform might hallucinate changes

 3. VERIFY MODIFICATIONS BEFORE FINALIZING
confirm_staged_changes  See what's actually prepared

 4. FINALIZE WITH EXPLICIT CONTEXT
finalize_with_context "feat(scope): specific functionality with validation"
```

 Platform-Safe Component Modification
```
 === COMPONENT: specific_implementation.py ===
 BEFORE MODIFICATION - SHOW CURRENT STATE
"""
CURRENT COMPONENT CONTENT (initial segment):
import required_modules
component_configuration
...

PROPOSED MODIFICATIONS:
1. Add error handling to external interactions
2. Implement retry mechanisms
3. Add data validation procedures
"""

 ACTUAL IMPLEMENTATION CHANGES...
```

 Data Source Implementation Pattern
```
 CORRECT - FREE SOURCE PRIORITY
def fetch_market_data():
     Primary: Free provider (no API key)
    data = fetch_from_primary_source()
    if data:
        return data
    
     Backup: Alternative provider (secondary)
    data = fetch_from_backup_source()
    if data:
        log_warning("Using backup data source")
        return data
    
     Fallback: No data available
    return None

 WRONG - DEFAULTING TO BACKUP
def fetch_market_data():
     Platform might incorrectly prioritize backup source
    return fetch_from_backup_source()  Violates cost rules
```

---

 🚫 PLATFORM-SPECIFIC BANNED BEHAVIORS

 Memory Assumption Violations
- ❌ "As we discussed" (without specific interaction reference)
- ❌ "In the previous implementation" (without component/line reference)
- ❌ "The existing code" (without showing actual implementation)
- ❌ Assuming platform remembers conversation from extended sequences

 Resource Hallucinations
- ❌ Creating paths that don't exist without verification
- ❌ Modifying components without showing current state first
- ❌ Assuming organizational structures without verification
- ❌ Referencing non-existent configuration elements

 Optimistic Implementation Patterns
- ❌ External calls without timeout and error handling
- ❌ Data operations without validation verification
- ❌ Resource operations without existence checks
- ❌ Assuming environment configuration is established

 Cost Violation Patterns
- ❌ Using backup data sources when primary is available
- ❌ Implementing paid services without explicit approval
- ❌ Adding API dependencies that incur costs
- ❌ Defaulting to authenticated services over free alternatives

---

 ✅ PLATFORM-SPECIFIC REQUIRED BEHAVIORS

 Reality Verification Rituals
```
 MANDATORY STARTING POINT FOR ANY TASK
verify_current_environment
confirm_project_structure
validate_reference_documents
```

 Context Anchoring
```
=== CONTEXT ANCHOR ===
Current Component: specific_implementation.py
Current Objective: Add error handling to external calls
Reference: architecture document specific sections
Last Action: Verified component existence
```

 Progress Tracking
```
=== PROGRESS TRACKER ===
Completed:
✅ Verified component structure
✅ Added error handling procedures
✅ Implemented retry mechanisms

Remaining:
⬜ Add data validation
⬜ Test with actual data
⬜ Update documentation
```

 Data Source Validation
```
=== SOURCE VALIDATION ===
Primary Source: Free external provider (verified available)
Backup Source: Alternative provider (confirmed as backup only)
Cost Status: Zero (primary source selected)
Authentication: None required (free access confirmed)
```

---

 💰 RESOURCE MANAGEMENT RULES

 Platform Resource Control Weaknesses
- ❌ WEAKNESS: May suggest intensive operations without impact analysis
- ✅ MITIGATION: Always check resource tracking documentation first
- ✅ PATTERN: "This operation requires X resources - confirm approval?"

 Data Source Cost Protocol
- ✅ PRIMARY: Free external providers (no authentication)
- ✅ BACKUP: Alternative sources (secondary, minimal usage)
- ❌ PROHIBITED: Paid services without explicit budget approval
- ❌ VIOLATION: Using backup sources when primary is functional

 Reality-Based Resource Verification
```
 CHECK ACTUAL USAGE BEFORE SUGGESTING NEW OPERATIONS
verify_current_resource_consumption
project_anticipated_usage
confirm_within_allocated_bounds
```

---

 🎯 PLATFORM PERFORMANCE OPTIMIZATION

 Optimal Context Window Usage
- ✅ SEGMENT SIZE: Process manageable portions per response
- ✅ COMPONENT FOCUS: One primary component per interaction sequence
- ✅ SUMMARY CYCLES: Summarize progress at regular intervals
- ❌ CONTEXT OVERLOAD: Don't load multiple complex components simultaneously

 Effective Interaction Patterns
```
GOOD: "Let's work on COMPONENT: specific/path - specifically the target_method functionality"
BAD:  "Improve the implementation" (insufficient specificity)

GOOD: "Based on specific sections of reference document, implement X"
BAD:  "Follow the plan" (no specific reference)
```

 Platform Memory Reinforcement
```
=== MEMORY REINFORCEMENT ===
Key operational constraints:
1. Project uses structured data architecture
2. No synthetic data allowed - ever
3. Critical integration = significant impact factor
4. Resource limit: established boundaries
5. All components need standard metadata
6. Data sources: Free primary, backup secondary only
```

---

 🚨 CRITICAL PERFORMANCE DECAY MITIGATION

 Inevitable Cognitive Degradation Protocol
```
=== DEGRADATION DETECTED ===
Observed: Platform performance degradation after extended use
Required: Full context reset and reality verification
Protocol: Execute comprehensive system check
```

 Extended Session Recovery Pattern
```
After 2+ hours of continuous operation:
1. PAUSE all complex implementations
2. VERIFY all assumptions from past hour
3. RESTATE current objective with fresh context
4. CONFIRM all referenced resources actually exist
5. RESUME with simplified, verified approach
```

 Reality Restoration Sequence
```
 WHEN PLATFORM BECOMES UNRELIABLE
emergency_reality_check
validate_all_referenced_components
confirm_current_implementation_state
restate_primary_objective_fresh
```

 Data Source Integrity Check
```
=== SOURCE INTEGRITY VERIFICATION ===
When platform performance degrades:
1. RE-VERIFY primary data source availability
2. CONFIRM backup source is still secondary
3. VALIDATE no cost violations introduced
4. ENSURE free provider remains primary
```

---

 📊 CURRENT PROJECT STATUS - PLATFORM AWARE

VERIFIED COMPONENTS: Confirmed via direct verification  
ACTUAL RESOURCE USAGE: Within established boundaries  
CRITICAL INTEGRATION: Significant impact factor identified  
PLATFORM CONTEXT: Recent interaction sequence documented  
DATA SOURCE STATUS: Free primary provider active, backup available but unused  

NEXT ACTION:
```
 VERIFY CURRENT STATE BEFORE PROCEEDING
confirm_component_structure
verify_data_resource_counts
validate_implementation_environment
```

---

Version: Agentic Platform Edition  
Enforcement: Active with platform weakness mitigation  
Weaknesses Addressed: Memory degradation, resource hallucinations, optimistic assumptions  
Performance Decay Protocol: Activated after 2+ hour sessions  
Data Source Protocol: Free primary, backup secondary only  
Next Reality Check: Every 10 interactions during critical integration



