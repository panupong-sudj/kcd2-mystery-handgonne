-- Mystery Handgonne Lua (loaded by the game as Scripts/mods/<modid>.lua).
--
-- 1. Reload x4: bind the reload buff (rpg/buff__mystery_handgonne.xml) to each gun item so it only applies while that
--    gun is equipped. Weapon rows have no buff field and the reload animation speed belongs to the crossbow
--    class, so ItemManager.AddOnEquipBuff is the only per-item hook. The player's inventory is scanned every few
--    seconds to catch guns that are forged, bought or spawned after loading.
-- 2. Thunderous Blast: the vanilla perk is C++ (Cpp:ThunderousBlast) and only reacts to real firearms (class 13),
--    so the first shot of this gun in a fight applies the perk's own debuff to everyone nearby who is in
--    combat, if the player has the perk.
MysteryHandgonne = MysteryHandgonne or {}

-- All forged versions of the gun (item__mystery_handgonne.xml): Masterwork, Crude, Standard.
local GUN_CLASSES = {
	["537e65b8-f6c8-4a74-964d-3bdde8319617"] = true, -- mystery_handgonne_masterwork (Masterwork)
	["3aa546fe-db34-492b-8471-b6d0049cfc2c"] = true, -- mystery_handgonne_crude
	["8dbef853-eca9-4121-927e-0bdf6281edf8"] = true, -- mystery_handgonne_standard
}
local RELOAD_BUFF = "7a553f9e-b8b0-423f-a7a6-ed3ac62719ca" -- mystery_handgonne_fast_reload (rls*4)
local THUNDER_PERK = "6ce5cd8b-360f-40f3-88d3-7647dd1b6f11" -- perk "Thunderous blast"
local THUNDER_DEBUFF = "d8c62af9-fde6-43b7-a36d-1f044987d552" -- perk_thunderous_blast_debuff (fencing-3, defense-3, courage*0.75, 20 s)
local THUNDER_RADIUS = 20
local SCAN_MS = 5000
-- 3. Starter recipes: once per save, put the gun sketch and the cartridge recipe book in the player's home stash.
--    (A ui/ExtraRewards row without DlcId/ProsId froze the game on load, so the DLC-reward route is out.)
--    The target is the level's player master chest (see FindHomeStashInventory); the items are created there
--    (see Deliver). Retries every scan until the chest is found; a hidden perk then marks the save. Everything
--    runs inside pcall.
local GIVEN_PERK = "d61014cd-b298-4683-8e92-0ab3fcc83963" -- "mystery_handgonne - recipes in stash"
local STARTER_ITEMS = {
	"cab9c097-ab8c-4f07-8c4f-35dcad7f9ce0", -- recipe_mystery_handgonne_sketch (blacksmith sketch)
	"b89c587e-3086-42e0-9ac8-8fc07d49f46d", -- recipe_mystery_handgonne_cartridge (alchemy recipe book)
}

local function log(msg)
	System.LogAlways("[mystery_handgonne] " .. msg)
end

local function truthy(v)
	return v and v ~= 0
end

function MysteryHandgonne:InCombat()
	return player and player.soul and truthy(player.soul:IsInCombatDanger())
end

function MysteryHandgonne:GunInHand()
	if not (player and player.human) then
		return false
	end
	for hand = 0, 1 do
		local ok, item = pcall(function() return player.human:GetItemInHand(hand) end)
		if ok and item then
			local inst = ItemManager.GetItem(item)
			if inst and GUN_CLASSES[inst.class] then
				return true
			end
		end
	end
	return false
end

-- Inventory a stash entity opens: its master inventory when linked to one, else its own (vanilla
-- Stash:GetInventoryToOpen in Scripts/Entities/WH/Stash/AnimStash.lua).
local function StashInventory(e)
	if e.GetInventoryToOpen then
		return e:GetInventoryToOpen()
	end
	local master = e.stash and e.stash:GetMasterInventory()
	if master and Framework.IsValidWUID(master) then
		return master
	end
	return e.inventoryId
end

-- Every level has one Stash entity named "stash[Chest/playerMasterChest_<guid>]" (layer Main/_script/playerStash):
-- the shared inventory behind all of the player's home stashes. Fallback: any Stash whose inventory the player owns
-- (the vanilla ownership test from Stash:UsesStealUiPrompt). Returns inventory id, name, entity.
function MysteryHandgonne:FindHomeStashInventory()
	local list = System.GetEntitiesByClass("Stash") or {}
	for _, e in ipairs(list) do
		local ok, name = pcall(function() return e:GetName() end)
		if ok and name and string.find(name, "playerMasterChest", 1, true) then
			local ok2, inv = pcall(StashInventory, e)
			if ok2 and inv and inv ~= 0 then
				return inv, name, e
			end
			log("master chest " .. name .. " has no inventory yet: " .. tostring(inv))
		end
	end
	for _, e in ipairs(list) do
		local ok, inv = pcall(function()
			local inv = StashInventory(e)
			if inv and inv ~= 0 and EntityModule.GetInventoryOwner(inv) == player.this.id then
				return inv
			end
		end)
		if ok and inv then
			return inv, e:GetName(), e
		end
	end
	return nil, "Stash=" .. #list
end

-- One starter item. ItemManager.CreateItem threw a Lua error for these Document items, so this uses
-- Inventory:CreateItem (vanilla ItemUtils.CreateInvItem), which creates the item straight inside an inventory:
--   1. in the stash entity's own inventory, when that is the one the stash opens;
--   2. else in the player's bag, then MoveItemOfClass to the stash (vanilla ItemUtils.GiveItem).
-- Returns where the item ended up: "stash", "bag" or nil.
local function Deliver(class, inv, e)
	local ok, r = pcall(function()
		local own = e and e.inventory
		if own and own.CreateItem and Framework.WUIDToMsg(own:GetId()) == Framework.WUIDToMsg(inv) then
			return own:CreateItem(class, 1, 1)
		end
		return "not own"
	end)
	if ok and r ~= "not own" and r ~= false and r ~= 0 then
		return "stash"
	end
	log("stash CreateItem " .. class .. ": " .. tostring(r))
	ok, r = pcall(function() return player.inventory:CreateItem(class, 1, 1) end)
	if not ok or r == false or r == 0 then
		log("bag CreateItem " .. class .. " failed: " .. tostring(r))
		return nil
	end
	local ok2, n = pcall(function() return player.inventory:MoveItemOfClass(inv, class, 1, true) end)
	if ok2 and (tonumber(n) or 0) > 0 then
		return "stash"
	end
	log("move " .. class .. " to stash: " .. tostring(n))
	return "bag"
end

function MysteryHandgonne:GiveStarterRecipes()
	if self.giveFailed or not (player and player.soul and player.inventory) or truthy(player.soul:HasPerk(GIVEN_PERK, false)) then
		return
	end
	local inv, info, e = self:FindHomeStashInventory()
	if not inv then
		if not self.waitLogged then
			self.waitLogged = true
			log("no player stash loaded yet (" .. tostring(info) .. "); will retry")
		end
		return
	end
	local result = {}
	local any = false
	for _, class in ipairs(STARTER_ITEMS) do
		local where = Deliver(class, inv, e)
		any = any or where ~= nil
		result[#result + 1] = class .. "=" .. tostring(where)
	end
	if any then
		player.soul:AddPerk(GIVEN_PERK)
	else
		self.giveFailed = true -- nothing could be created: stop retrying until the next game start
	end
	log("starter recipes (" .. tostring(info) .. "): " .. table.concat(result, ", "))
end

function MysteryHandgonne:Scan()
	local ok, err = pcall(function() MysteryHandgonne:GiveStarterRecipes() end)
	if not ok and not self.giveErrLogged then
		self.giveErrLogged = true
		log("starter recipes failed: " .. tostring(err))
	end
	if player and player.inventory then
		for class in pairs(GUN_CLASSES) do
			local item = player.inventory:FindItem(class)
			if truthy(item) then
				local key = tostring(item)
				if not self.bound[key] then
					ItemManager.AddOnEquipBuff(item, RELOAD_BUFF, true)
					self.bound[key] = true
					log("reload buff bound to gun " .. key .. " (" .. class .. ")")
				end
			end
		end
	end
	if not self:InCombat() then
		self.blasted = false -- the next fight gets a new first shot
	end
	Script.SetTimer(SCAN_MS, function() MysteryHandgonne:Scan() end)
end

function MysteryHandgonne:OnShot()
	if not self:InCombat() then
		self.blasted = false
		return
	end
	if self.blasted or not truthy(player.soul:HasPerk(THUNDER_PERK, false)) then
		return
	end
	self.blasted = true
	local hit = 0
	for _, e in ipairs(System.GetEntitiesInSphere(player:GetWorldPos(), THUNDER_RADIUS) or {}) do
		if e ~= player and e.soul and e.actor and not truthy(e.actor:IsDead()) and truthy(e.soul:IsInCombatDanger()) then
			e.soul:AddBuff(THUNDER_DEBUFF)
			hit = hit + 1
		end
	end
	log("thunderous blast: debuffed " .. hit .. " nearby")
end

function MysteryHandgonne:HookActions()
	if self.hooked or not Player then
		return
	end
	self.hooked = true
	local previous = Player.OnAction
	function Player:OnAction(action, activation, value)
		-- Aim = crossbow_prepare press; stop aiming = crossbow_abort release (both on the right mouse button).
		-- A crossbow_execute press while aiming is a shot; one while not aiming is a reload click.
		if action == "crossbow_prepare" and activation == "press" then
			MysteryHandgonne.aiming = true
		elseif action == "crossbow_abort" and activation == "release" then
			MysteryHandgonne.aiming = false
		elseif action == "crossbow_execute" and activation == "press" and MysteryHandgonne.aiming and MysteryHandgonne:GunInHand() then
			MysteryHandgonne:OnShot()
		end
		if previous then
			return previous(self, action, activation, value)
		end
	end
	log("action hook installed")
end

function MysteryHandgonne:OnGameplayStarted()
	-- Every load starts from fresh item objects, so bind again.
	self.bound = {}
	self.blasted = false
	self.giveFailed = false
	self:HookActions()
	if not self.scanning then
		self.scanning = true
		self:Scan()
	end
end

-- 4. Console commands (the console needs the game started with -devmode). Items are created straight in the
--    player's bag with Inventory:CreateItem (ItemManager.CreateItem fails for the Document items).
local GUN_BY_NAME = {
	crude = "3aa546fe-db34-492b-8471-b6d0049cfc2c",
	standard = "8dbef853-eca9-4121-927e-0bdf6281edf8",
	masterwork = "537e65b8-f6c8-4a74-964d-3bdde8319617",
}
local CARTRIDGE = "5bc60b91-ce2d-401b-9dfc-8da0e719401a"
-- One forging: the smithing recipe's ingredients (minigame/BlacksmithRecipes__mystery_handgonne.xml).
local FORGE_MATERIALS = {
	{ "92aa6120-028e-48ee-8ed1-1c5f91afaa26", 3 },
	{ "3c1c0ae2-731e-40c1-a917-024fb3f000da", 2 },
	{ "4a4da84c-f12a-4bc8-94dc-a7d8d76788ea", 2 },
	{ "4a6269c1-5c01-473d-ad69-e0a0c41643e7", 3 },
}
-- One brew: oil base (vanilla alchemyOil) + saltpetre, sulphur, charcoal (minigame/AlchemyRecipe__mystery_handgonne.xml).
local BREW_MATERIALS = {
	{ "34bd1d0b-1203-42a0-b9b4-d3585a4d9b48", 1 },
	{ "8cf956d4-39d6-4e9d-9010-95f8f2772ad9", 1 },
	{ "0513eeae-05a8-4ca7-8719-443cb0d906d5", 1 },
	{ "f879ac63-2ce2-4114-83a2-89643c1ed102", 1 },
}

-- A console argument: empty when none was typed (the engine may leave the "%1" placeholder in place).
local function Arg(a)
	a = tostring(a or "")
	if a == "" or string.sub(a, 1, 1) == "%" then
		return ""
	end
	return string.lower(a)
end

local function Give(class, amount)
	local ok, r = pcall(function() return player.inventory:CreateItem(class, 1, amount) end)
	if not ok or r == false then
		log("console: could not create " .. class .. ": " .. tostring(r))
		return false
	end
	return true
end

function MysteryHandgonne:CmdGun(which)
	which = Arg(which)
	local class = GUN_BY_NAME[which ~= "" and which or "masterwork"]
	if not class then
		log("usage: mystery_handgonne_gun [crude|standard|masterwork]")
		return
	end
	if Give(class, 1) then
		log("console: gun added to the bag (" .. (which ~= "" and which or "masterwork") .. ")")
	end
end

function MysteryHandgonne:CmdAmmo(count)
	count = tonumber(Arg(count)) or 40
	if Give(CARTRIDGE, count) then
		log("console: " .. count .. " cartridges added to the bag")
	end
end

function MysteryHandgonne:CmdRecipes()
	for _, class in ipairs(STARTER_ITEMS) do
		Give(class, 1)
	end
	log("console: sketch and recipe book added to the bag")
end

function MysteryHandgonne:CmdMaterials(times)
	times = tonumber(Arg(times)) or 1
	for _, list in ipairs({ FORGE_MATERIALS, BREW_MATERIALS }) do
		for _, e in ipairs(list) do
			Give(e[1], e[2] * times)
		end
	end
	log("console: materials for " .. times .. " forging(s) and brew(s) added to the bag")
end

function MysteryHandgonne:CmdAll()
	self:CmdGun("masterwork")
	self:CmdAmmo(40)
	self:CmdRecipes()
	self:CmdMaterials(1)
end

System.AddCCommand("mystery_handgonne_gun", 'MysteryHandgonne:CmdGun("%1")',
	"Mystery Handgonne: add a gun to the bag. Optional: crude | standard | masterwork (default)")
System.AddCCommand("mystery_handgonne_ammo", 'MysteryHandgonne:CmdAmmo("%1")',
	"Mystery Handgonne: add cartridges to the bag. Optional count (default 40)")
System.AddCCommand("mystery_handgonne_recipes", "MysteryHandgonne:CmdRecipes()",
	"Mystery Handgonne: add the gun sketch and the cartridge recipe book to the bag")
System.AddCCommand("mystery_handgonne_materials", 'MysteryHandgonne:CmdMaterials("%1")',
	"Mystery Handgonne: add materials for one forging and one brew. Optional multiplier (default 1)")
System.AddCCommand("mystery_handgonne_all", "MysteryHandgonne:CmdAll()",
	"Mystery Handgonne: masterwork gun, 40 cartridges, both recipes and one set of materials")

UIAction.RegisterEventSystemListener(MysteryHandgonne, "System", "OnGameplayStarted", "OnGameplayStarted")
log("script loaded")
