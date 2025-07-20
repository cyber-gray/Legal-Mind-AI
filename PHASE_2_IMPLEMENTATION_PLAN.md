# Phase 2 Implementation Plan: Direct Orchestrator → Azure Agents Service

## 📋 **Conceptual Mapping Analysis**

Based on the provided mapping, here's our current state vs target implementation:

### ✅ **Already Completed (Phase 1)**
| Component | Current State | Status |
|-----------|---------------|--------|
| **Inline Instruction Strings** | ✅ Modular prompts framework created | Framework Ready |
| **Quality Score in Prompt** | ✅ External quality scorer implemented | Complete |
| **Manual Agent Selection** | ✅ Heuristic system working | Phase 1 Complete |

### 🔧 **Ready for Implementation (Phase 2)**

#### **1. Agent Instructions → Persisted Resource**
```python
# CURRENT: Inline strings in code
instructions="""You are a PolicyAnalyst..."""

# TARGET: Agent instructions as persisted resource
agent = await project_client.agents.create_agent(
    model="gpt-4",
    name="PolicyAnalyst", 
    instructions=self._load_prompt("policy_analyst.md"),
    tools=[]
)
```

#### **2. Process Group Chat → Thread + Sequential Runs**
```python
# CURRENT: Manual orchestration in process_group_chat()
coord_response = await self.get_agent_response(self.COORDINATOR, query)

# TARGET: Thread-based conversation with runs
thread = await self.project_client.agents.create_thread()
run = await self.project_client.agents.create_run(
    thread_id=thread.id,
    assistant_id=coordinator_agent.id
)
```

#### **3. Manual Agent Selection → Planner Agent/Tool**
```python
# CURRENT: Keyword heuristics in _determine_needed_agents()
if 'policy' in query_lower:
    needed_agents.append(self.POLICY_ANALYST)

# TARGET: Planner agent with tool delegation
planner_agent = await self._create_planner_agent()
delegation_plan = await self._get_delegation_plan(query)
```

#### **4. Blob JSON → Native Thread Persistence**
```python
# CURRENT: Manual blob storage
await self._save_conversation_to_storage(conversation_data)

# TARGET: Native thread persistence
# Automatic persistence with optional export
thread_messages = await project_client.agents.list_messages(thread_id)
```

#### **5. Direct Calls → AgentsClient Primitives**
```python
# CURRENT: Direct AzureChatCompletion calls
response = await self.kernel.invoke(agent_function, input=user_input)

# TARGET: Agents Service primitives
run = await project_client.agents.create_and_poll_run(
    thread_id=thread.id,
    assistant_id=agent.id,
    additional_instructions=context
)
```

#### **6. Quality Score → Post-run Evaluation Tool**
```python
# CURRENT: Embedded in prompt instructions
"Score your analysis quality from 1-10..."

# TARGET: Separate evaluation function/tool
@kernel_function
async def evaluate_response_quality(
    response: str, 
    query: str, 
    agent_type: str
) -> Dict[str, Any]:
    return self.quality_scorer.analyze_response_quality(response, query, agent_type)
```

#### **7. Future APIs → Registered Function Tools**
```python
# TARGET: Function tools for external data
@kernel_function
async def search_legal_database(query: str) -> List[Dict]:
    """Search external legal database for relevant cases"""
    return await self.legal_db_client.search(query)

@kernel_function  
async def get_news_updates(topic: str) -> List[Dict]:
    """Get recent legal news and updates"""
    return await self.news_client.get_updates(topic)
```

## 🚀 **Phase 2 Implementation Strategy**

### **Step 1: Azure AI Project Setup**
1. **Create AI Studio Project** with proper region (East US, West Europe, etc.)
2. **Configure Agents API access** and verify model availability
3. **Set up connection strings** for the experimental version

### **Step 2: Agent Creation Migration**
1. **Convert agent configs** to Azure Agents Service
2. **Upload modular prompts** as agent instructions
3. **Test individual agent creation** and responses

### **Step 3: Thread-Based Conversations**
1. **Replace process_group_chat()** with thread management
2. **Implement sequential runs** with coordinator synthesis
3. **Add native persistence** with optional blob export

### **Step 4: Enhanced Agent Selection**
1. **Keep current heuristics** (Phase 1 approach - lower risk)
2. **Future: Add planner agent** (Phase 2 enhancement)
3. **Progressive migration** to reduce implementation risk

### **Step 5: Function Tools Integration**
1. **Quality scoring as function tool**
2. **External data sources** (legal databases, news)
3. **Custom evaluation functions**

## 📝 **Implementation Priority**

### **High Priority (This Week)**
- [ ] Azure AI Studio project setup
- [ ] Basic agent creation with modular prompts
- [ ] Thread-based conversation flow
- [ ] Quality scoring as function tool

### **Medium Priority (Next Week)**
- [ ] Sequential runs with coordinator synthesis
- [ ] Native thread persistence
- [ ] Enhanced error handling with correlation IDs
- [ ] Performance optimization

### **Lower Priority (Future)**
- [ ] Planner agent for dynamic delegation
- [ ] External function tools (legal DB, news)
- [ ] Advanced evaluation metrics
- [ ] Web interface integration

## 🎯 **Success Criteria**

### **Technical KPIs**
- **Agent Creation**: All 5 agents created in Azure Agents Service
- **Thread Management**: Proper conversation persistence
- **Response Quality**: Maintain 9+ average quality scores
- **Performance**: <5 second response times (acceptable increase from direct calls)

### **Migration Validation**
- **Functional Parity**: Same quality responses as direct orchestrator
- **Enhanced Features**: Better persistence and audit trails
- **Reduced Complexity**: Simplified conversation management
- **Future Ready**: Foundation for function tools and external data

## 🔧 **Next Actions**

1. **Set up Azure AI Studio project** in supported region
2. **Create foundry agents version** in experimental file
3. **Implement thread-based conversation flow**
4. **Test quality scoring as function tool**
5. **Validate against production system performance**

This mapping provides the perfect roadmap for evolving from our current direct orchestrator to a fully managed Azure Agents Service architecture while preserving all the quality and functionality we've built!
