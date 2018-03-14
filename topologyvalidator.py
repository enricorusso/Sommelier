from toscaparser.elements.entity_type import EntityType
from toscaparser.tosca_template import ToscaTemplate

class TopologyValidator():

	customDefinition = {}
	toscaBaseTypes = {}

	# Checks whether type1 is coherent with type2 (i.e., whether type1 is the same type or a sub-type of type2)
	def checkTypeCoherence(self, type1, type2):

		passed = (type1 == type2)

		if self.customDefinition.has_key(type1):
			type1def = self.customDefinition.get(type1)
		else:
		    type1def = self.toscaBaseTypes.get(type1)

		if type1def is not None:
			while (passed == False and type1def.has_key('derived_from')):
					type1 = type1def.get('derived_from')
					if type1 == type2:
						passed = True
					type1 = type1def.get('derived_from')
					if self.customDefinition.has_key(type1):
						type1def = self.customDefinition.get(type1)
					else:
						type1def = self.toscaBaseTypes.get(type1)
		return passed

	# Returns the definition of the requirement "reqName" in the node type "nodeType" (if any)
	def getRequirementDefinition(self, reqName, nodeType):
		nodeTypeDef = self.getTypeDefinition(nodeType)

		# check whether "nodeType" defines "reqName"
		reqDef = None
		if nodeTypeDef.has_key("requirements"):
			# reqDefinitions = nodeTypeDef.get('requirements')[0]
			for reqDefinitions in nodeTypeDef.get('requirements'):
				if reqName in reqDefinitions:
					reqDef = reqDefinitions.get(reqName)

		# if "reqName" has been found, returns the corresponding "reqDef"
		if reqDef is not None:
			return reqDef
		# otherwise, looks for "capName" in the parent "nodeType"
		if nodeTypeDef.has_key('derived_from'):
			return self.getRequirementDefinition(reqName,nodeTypeDef.get('derived_from'))
		# if there is no parent "nodeType", returns "None"
		return None

	# Returns the definition of the capability "capName" in the node type "nodeType" (if any)
	def getCapabilityDefinition(self, capName, nodeType):
		nodeTypeDef = self.getTypeDefinition(nodeType)

		# check whether "nodeType" defines "capName"
		capDef = None
		if nodeTypeDef.has_key("capabilities"):
			capDefinitions = nodeTypeDef.get('capabilities')
			if capName in capDefinitions:
				capDef = capDefinitions.get(capName)

		# if "capName" has not been found, looks for "capName" in the parent "nodeType" (if any)
		if capDef is None and nodeTypeDef.has_key('derived_from'):
			return self.getCapabilityDefinition(capName,nodeTypeDef.get('derived_from'))

		return capDef

	# Returns the definition of the node with type "nodeType" (if any)
	def getTypeDefinition(self, nodeType):
		typeDef = None

		if self.customDefinition.has_key(nodeType):
			typeDef = self.customDefinition.get(nodeType)
		elif self.toscaBaseTypes.has_key(nodeType):
		    typeDef = self.toscaBaseTypes.get(nodeType)

		return typeDef

	# Returns the node template of the node called "nodeName" (if any)
	def getNode(self, nodeName, nodeTemplates):
		# Assigns the type of "nodeTemplate" to "nodeType"
		node = None
		for n in nodeTemplates:
			if n.name == nodeName:
				node = n
		return node

	# Check whether the "node_type_name" of the requirement definition "reqDef" is coherent with "nodeType"
	def checkNodeType(self, reqDef, nodeType):
		if reqDef.has_key('node'):
			reqDefNodeType = reqDef.get('node')
			return self.checkTypeCoherence(nodeType, reqDefNodeType)
		return True

	# Returns the type of the capability "capability"
	def getCapabilityType(self, capability, node):
		capabilityType = None

		if capability in self.toscaBaseTypes or capability in self.customDefinition:
			capabilityType = capability
		else:
			if self.getCapabilityDefinition(capability, node.type) is not None:
				if self.getCapabilityDefinition(capability, node.type).has_key('type'):
					capabilityType = self.getCapabilityDefinition(capability, node.type).get('type')
		return capabilityType

	# Check whether the the type of the capability "capability" is coherent with the type of the capability defined from the requirement definition "reqDef"
	def checkCapabilityType(self, reqDef, capability, node):

		# Assigns the capability type of the requirement definition to "reqDefCap"
		if reqDef.has_key('capability'):
			reqDefCap = reqDef.get('capability')

			capabilityType = self.getCapabilityType(capability, node)
			return self.checkTypeCoherence(capabilityType, reqDefCap)
		return True

	# Check whether the type of the capabilities of "capabilityList" are coherent with the type of the capability defined from the requirement definition "reqDef"
	def checkCapabilitiesType(self, reqDef, capabilityList, node):

		for capability in capabilityList:
			if self.checkCapabilityType(reqDef,capability,node) == True:
				return True
		return False

	# Returns the type of the relationship "relationship"
	def getRelationshipType(self, relationship, node):

		if type(relationship) is dict:
			if relationship.has_key('type'):
				relationshipType = relationship.get('type')
		else:
			if relationship in self.toscaBaseTypes or relationship in self.customDefinition:
				relationshipType = relationship
			else:
				for rt in node.get_relationship_template():
					if rt.name == relationship:
						relationshipType = rt.type
		return relationshipType

	# Check whether the type of the relationship "relationship" is coherent with the type defined from the relationship definition "reqDef"
	def checkRelationshipType(self, reqDef, relationship, node):

		# Assigns the relationship type of the requirement definition to "reqDefRel"
		if reqDef.has_key('relationship'):
			reqDefRel = reqDef.get('relationship')
			if type(reqDefRel) is dict:
				if reqDefRel.has_key('type'):
					reqDefRel = reqDefRel.get('type')

			# Assigns the relationship type to "relationshipType"
			relationshipType = self.getRelationshipType(relationship,node)

			# Check whether "reqDefRel" is coherent with "relationshipType"
			return self.checkTypeCoherence(relationshipType, reqDefRel)

	# Check whether the relationship is valid and return the type of the target capability or None
	def checkRelationship(self, reqDef, relationship, targetNode, node, targetCapability):

		# Assigns the relationship type of the requirement definition to "reqDefRel"
		if reqDef.has_key('relationship'):
			reqDefRel = reqDef.get('relationship')
			if type(reqDefRel) is dict:
				if reqDefRel.has_key('type'):
					reqDefRel = reqDefRel.get('type')

			# Assigns the relationship type to "relationshipType"
			relationshipType = self.getRelationshipType(relationship,node)

			######### CONTROLLI PUNTO 2 #########

			# Assigns the valid_target_types of the relationship to "validTargetTypes"
			validTargetTypes = self.getValidTargetTypes(relationshipType)
			if validTargetTypes is not [] and validTargetTypes is not None: # PASSA LA VERIFICA
				# Case 1 - the relationship_template of the target is a capability
				if targetCapability is not None:
					# Assigns the capability type of the "target capability" to "targetCapabilityType"
					targetCapabilityType = self.getCapabilityType(targetCapability,targetNode)
					# Check whether the capability type is coherent with the capabilities type of the valid_target_type
					for validTargetType in validTargetTypes:
						if self.checkTypeCoherence(targetCapabilityType,validTargetType) == True:
							return targetCapabilityType
					return None
				# Case 2 - the relationship_template of the target is a node
				else:
					# Retrieves the capabilities of the target node
					targetCapabilities = targetNode.get_capabilities()
					# Check whether the capability type of the target node are coherent with the capabilities type of the valid_target_type
					for cap in targetCapabilities:
						capType = self.getCapabilityType(cap,targetNode)
						for validTargetType in validTargetTypes:
							if self.checkTypeCoherence(capType,validTargetType) == True:
								return capType
					return None

	# Returns the field "valid_target_types" of the relationship with type "relationshipType"
	def getValidTargetTypes(self, relationshipType):

		relationshipTypeDef = self.getTypeDefinition(relationshipType)

		validTargetTypes = None
		if relationshipTypeDef.has_key("valid_target_types"):
				validTargetTypes = relationshipTypeDef.get('valid_target_types')

		# if "validTargetTypes" has been found, returns the "valid_target_types"
		if validTargetTypes is not None:
			return validTargetTypes
		# otherwise, looks for "validTargetTypes" in the parent "relationshipType" (if any)
		if relationshipTypeDef.has_key("derived_from"):
			return self.getValidTargetTypes(relationshipTypeDef.get('derived_from'))
		# if there is no parent "relationship", returns "None"
		return None

	# Returns the field "valid_source_types" of a node with type "nodeType"
	def getValidSourceTypesNode(self, capabilityType, nodeType):

		nodeTypeDef = self.getTypeDefinition(nodeType)

		validSourceTypes = None
		if nodeTypeDef.has_key("capabilities"):
			capabilities = nodeTypeDef.get('capabilities')
			for cap in capabilities.values():
				if cap.get('type') == capabilityType:
					validSourceTypes = cap.get('valid_source_types')

		# if "validSourceTypes" has been found, returns the "valid_source_types"
		if validSourceTypes is not None:
			return validSourceTypes
		# otherwise, looks for "validTargetTypes" in the parent "nodeType" (if any)
		if nodeTypeDef.has_key("derived_from"):
			return self.getValidSourceTypesNode(capabilityType,nodeTypeDef.get('derived_from'))
		# if there is no parent "nodeType", returns "None"
		return None

	# Check whether the types of the nodes defined from the field "valid_source_types" of a "target node" are coherent with the type of a "source node"
	def checkValidSourceTypesNode(self, targetCapabilityType, targetNode, node):

		validSourceTypes = self.getValidSourceTypesNode(targetCapabilityType,targetNode.type)

		if validSourceTypes is not None:
			for elem in validSourceTypes:
				if self.checkTypeCoherence(node.type,elem) is True:
					return True
			return False
		return True

	# Returns the field "valid_source_types" of a capability with type "capabilityType"
	def getValidSourceTypesCapability(self, capabilityType):

		capTypeDef = self.getTypeDefinition(capabilityType)

		validSourceTypes = None
		if capTypeDef.has_key("valid_source_types"):
			validSourceTypes =  capTypeDef.get('valid_source_types')

		# if "validSourceTypes" has been found, returns the "valid_source_types"
		if validSourceTypes is not None:
			return validSourceTypes
		# otherwise, looks for "validSourceTypes" in the parent "capType"
		if capTypeDef.has_key("derived_from"):
			return self.getValidSourceTypesCapability(capTypeDef.get('derived_from'))
		# if there is no parent "nodeType", returns "None"
		return None

	# Check whether the types of the nodes defined from the field "valid_source_types" of a capability are coherent with the type of a "source node"
	def checkValidSourceTypesCapability(self, capabilityType, node):

		validSourceTypes = self.getValidSourceTypesCapability(capabilityType)

		if validSourceTypes is not None:
			for elem in validSourceTypes:
				if self.checkTypeCoherence(node.type,elem) == True:
					return True
			return False
		return True

	# Returns a structure with the summarize of the validation
	def validate(self, path):

	    serviceTemplate = ToscaTemplate(path, None, True)
	    self.toscaBaseTypes = EntityType.TOSCA_DEF
	    self.customDefinition = serviceTemplate._get_all_custom_defs()
	    validation = {}

	    if hasattr(serviceTemplate, 'nodetemplates'):
	        nodetemplates = serviceTemplate.nodetemplates
	        if nodetemplates:
	            for node in nodetemplates:

	                relationshipNode = []
	                capabilityNode = []

	                reqs = node.requirements
	                rName = None

	                validation[node.name] = {}

	                for r in reqs:
	                    rName = r.keys()[0]
	                    reqError = []

	                    # Gets the requirement definition of "rName"
	                    reqDef = self.getRequirementDefinition(rName,node.type)
	                    if (reqDef is None):
	                        reqError.append([1.1])
	                    else:
	                        # Isolates the names of the target node and capability
	                        targetNode = None
	                        targetCapability = None
	                        relationship = None

	                        if  type(r.get(rName)) == str:
	                            targetNode = r.get(rName)
	                        else:
	                            rProps = r.get(rName)
	                            # If "node" is defined, assigns it to "targetNode"
	                            if "node" in rProps:
	                                targetNode = rProps.get("node")
	                            # If "capability" is defined, assigns it to "targetCapability"
	                            if "capability" in rProps:
	                                targetCapability = rProps.get("capability")
	                            # If "relationship" is defined, assigns it to ""
	                            if "relationship" in rProps:
	                                relationship = rProps.get("relationship")

	                        # Retrieves the dictionary defining the target node
	                        targetNode = self.getNode(targetNode,nodetemplates)

	                        # Check if there is a target node
	                        if targetNode is None:
	                        	reqError.append([1.1])
	                        	validation[node.name].update({rName: reqError})
	                        	break

	                        # Checks whether the target node type is coherent with that declared in "reqDef"
	                        if (self.checkNodeType(reqDef,targetNode.type) is False):
	                            reqError.append([1.2, targetNode.type, targetNode.name])

	                        # Assigns the capability type of the target node to "targetCapabilityType"
	                        if targetCapability is not None:
	                            # Checks whether the target node capability is coherent with that declared in "reqDef"
	                            if self.checkCapabilityType(reqDef, targetCapability, targetNode) is False:
	                                reqError.append([1.3])

	                        else:
	                            # Retrieves the capabilities of the target node
	                            targetCapabilities = targetNode.get_capabilities()

	                            # Checks whether at least a target node capability is coherent with that declared in "reqDef"
	                            if self.checkCapabilitiesType(reqDef,targetCapabilities,targetNode) == False:
	                                reqError.append([1.4, targetNode.name, reqDef.get("capability")])

	                        # Assigns the relationship type of the target node to "relationshipType"
	                        if relationship is not None:

	                        	# Check whether the type of the relationship is coherent with that declared in "reqDef"
	                            if self.checkRelationshipType(reqDef,relationship,node) == False:
	                                reqError.append([1.5, targetNode.name])

	                            # Assigns the type of the target capability to "targetCapabilityType"
	                            targetCapabilityType = self.checkRelationship(reqDef,relationship,targetNode,node,targetCapability)
	                            # Case 1 - the "targetCapabilityType" is not valid
	                            if targetCapabilityType is None:
	                            	# Case 1.1 - the targetCapability is defined, but its type is not valid with that required
	                            	if targetCapability is not None:
	                            		reqError.append([2.1, targetCapability])
	                            	# Case 1.2 - the targetCapability is not defined and the target node does not offer valid capabilities
	                            	else:
	                            		reqError.append([2.2, targetNode.name])
	                            # Case 2 - the targetCapabilityType is defined
	                            else:
									# Case 2.1 - check whether the type of the target capability is coherent with that defined from the target capability definition
	                            	if self.checkValidSourceTypesCapability(targetCapabilityType,node) == False:
	                            		reqError.append([3.1, node.type])
	                            	# Case 2.2 - check whether the type of the target capability is coherent with that defined from the target node definition
	                            	if self.checkValidSourceTypesNode(targetCapabilityType,targetNode,node) == False:
	                            		reqError.append([3.2, node.type, targetNode.name])

	                    validation[node.name].update({rName: reqError})


	    return validation
