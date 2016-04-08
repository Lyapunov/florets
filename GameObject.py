import copy
import sys

class GameSolver:

   def solveInternal( self, game, solution ):
      if game.won():
         return True
      pathToWin = game.game_internal.find_path_between_rooms( lambda x : x == game.game_internal.final_room, game.game_internal.room.name, [], [] )
      if not pathToWin is None:
         self.do_for_all( game, solution, 'go', pathToWin )
         return self.solveInternal( game, solution )
      uses = game.game_internal.applicable_uses()
      if not uses == []:
         self.use_all( game, solution, uses )
         return self.solveInternal( game, solution )
      takes = game.game_internal.room.mobile_child_names()
      if not takes == []:
         self.do_for_all( game, solution, 'take', takes )
         return self.solveInternal( game, solution )
      opens = game.game_internal.room.openable_child_names()
      if not opens == []:
         self.do_for_all( game, solution, 'open', opens )
         return self.solveInternal( game, solution )
      pathToCanAnythingToDo = game.game_internal.find_path_between_rooms( lambda x : game.game_internal.can_anything_to_do( x ), game.game_internal.room.name, [], [] )
      if not pathToCanAnythingToDo is None:
         self.do_for_all( game, solution, 'go', pathToCanAnythingToDo )
         return self.solveInternal( game, solution )
      return True

   def do_for_all( self, game, solution, command, stuffs ):
      for stuff in stuffs:
         game.do_it( command, stuff )
         solution.append( [command, stuff ] ) 

   def use_all( self, game, solution, uses ):
      for [first, second] in uses:
         game.do_it( 'use', first, second )
         solution.append( ['use', first, second ] ) 
      
   def solve( self, game, use_checker = True ):
      if use_checker and not GameSyntaxChecker().check( game ) == '':
         return None
      my_solution = []
      my_game = copy.deepcopy( game )
      won = self.solveInternal( my_game, my_solution )
      if won:
         return my_solution
      return None

class GameSyntaxChecker:
   def check_must_have_at_least_one_room( self, game ):
      return len( game.game_internal.rooms ) > 0

   def check_final_room_differs_from_starting_room( self, game ):
      if ( len( game.game_internal.rooms ) > 0 ):
         if ( game.game_internal.final_room == game.game_internal.rooms[0].name ):
             return False
      return True
      
   def check_final_room_exists( self, game ):
      if ( not game.game_internal.find_room( game.game_internal.final_room ) is None ):
         return True
      return False

   def get_all_stuffs( self, game, addrooms = 0, add_top_children = 1 ):
      retval = []
      for room in game.game_internal.rooms:
         if addrooms == 1:
            retval += [ room ]
         retval += room.descendants( add_top_children )
      allactions = game.game_internal.use_actions
      for action in allactions:
         retval += action.get_prototype()
      return retval

   def get_all_stuff_names( self, game, addrooms = 0, add_top_children = 1 ):
      retval = []
      for stuff in self.get_all_stuffs( game, addrooms, add_top_children ):
         retval.append( stuff.name )
      return retval

   def get_list_of_accessible_rooms( self, game ):
      first_room = game.game_internal.rooms[0].name
      return game.game_internal.accessible_room_names( first_room )

   def check_final_room_is_reachable( self, game ):
      accessible_rooms = self.get_list_of_accessible_rooms( game )
      return game.game_internal.final_room in accessible_rooms

   def check_all_room_is_reachable( self, game ):
      accessible_rooms = self.get_list_of_accessible_rooms( game )
      for room in game.game_internal.rooms:
         if not room.name in accessible_rooms:
            return False
      return True

   def check_no_multiple_passages_between_rooms( self, game ):
      ordered_edges = []
      for passage in game.game_internal.passages:
         edge = passage.get_ordered_name()
         if edge in ordered_edges:
            return False
         else:
            ordered_edges.append( edge )
      return True

   def check_all_passage_identifiers_are_unique( self, game ):
      ids = []
      for passage in game.game_internal.passages:
         identifier = passage.identifier
         if identifier in ids:
            return False
         else:
            ids.append( identifier )
      return True

   def check_passage_identifiers_are_valid_in_actions( self, game ):
      ids = []
      for passage in game.game_internal.passages:
         ids.append( passage.identifier )
      allactions = game.game_internal.use_actions + game.game_internal.views
      for passage in allactions:
         try:
            if not passage.get_passage_identifier() in ids:
               return False
         except Exception:
            sys.exc_clear()
      return True

   def check_actors_are_valid_in_actions( self, game, allactions, include_rooms ):
      stuffs = self.get_all_stuff_names( game, include_rooms )
      for action in allactions:
         for actor in action.get_actor_names():
            if not actor == '' and not actor in stuffs:
               return False
      return True

   def check_no_actions_without_actors( self, game ):
      allactions = game.game_internal.use_actions + game.game_internal.views
      for action in allactions:
         for actor in action.get_actor_names():
            if not actor == '':
               break
         else:
            return False
      return True

   def check_no_actions_with_same_actor_twice( self, game ):
      allactions = game.game_internal.use_actions + game.game_internal.views
      for action in allactions:
         actors = action.get_actor_names()
         if actors[0] == actors[1]:
            return False
      return True

   def check_no_multiple_actions( self, game ):
      allactions = game.game_internal.use_actions + game.game_internal.views
      actor_pairs = []
      for action in allactions:
         pair = action.get_actor_names()
         if pair in actor_pairs:
            return False
         else:
            actor_pairs.append( pair )

      actors = []
      for action in allactions:
         if action.is_brutal():
            for actor in action.get_actor_names():
               if actor in actors:
                  return False
               else:
                  actors.append( actor )
      for action in allactions:
         if not action.is_brutal():
            for actor in action.get_actor_names():
               if actor in actors:
                  return False
      return True

   def check_no_two_actors_with_the_same_name( self, game ):
      stuffs = []
      for stuffname in self.get_all_stuff_names( game, 1 ):
         if stuffname in stuffs:
            return False
         else:
            stuffs.append( stuffname )
      return True

   def check_not_top_level_stuffs_cannot_have_attributes( self, game ):
      for stuff in self.get_all_stuffs( game, 0, 0 ):
         if len( stuff.get_attributes() ) > 0:
            return False
      return True

   def check( self, game ):
      if not self.check_must_have_at_least_one_room( game ):
         return "must have at least one room"

      if not self.check_final_room_differs_from_starting_room( game ):
         return "cannot start in the ending room"

      if not self.check_final_room_exists( game ):
         return 'final room does not exist'

      if not self.check_final_room_is_reachable( game ):
         return 'final room is not reachable' 

      if not self.check_no_multiple_passages_between_rooms( game ):
         return 'multiple passages between the same rooms'

      if not self.check_all_passage_identifiers_are_unique( game ):
         return 'passage identifiers are not unique'

      if not self.check_all_room_is_reachable( game ):
         return 'not all rooms are accessible'

      if not self.check_passage_identifiers_are_valid_in_actions( game ):
         return 'invalid passage identifiers in an action'

      if not self.check_actors_are_valid_in_actions( game, game.game_internal.use_actions, 0 ) or not self.check_actors_are_valid_in_actions( game, game.game_internal.views, 1 ):
         return 'found invalid object in an action'

      if not self.check_no_two_actors_with_the_same_name( game ):
         return 'found two objects with the same name'

      if not self.check_no_actions_without_actors( game ):
         return 'found an action without actors'

      if not self.check_no_actions_with_same_actor_twice( game ):
         return 'found invalid action with the same actor twice'

      if not self.check_no_multiple_actions( game ):
         return 'found multiple actions for the same actor'

      if not self.check_not_top_level_stuffs_cannot_have_attributes( game ):
         return 'not top level stuffs cannot have attributes'

      return ''


class Game:
   def __init__(  self, rooms, passages, use_actions, views, final_room ):
      self.game_internal = GameInternal( rooms, passages, use_actions, views, final_room )

   # === Reading the status of the game board ===

   def look( self ):
      return self.game_internal.look()

   def directions( self ):
      return self.game_internal.directions()

   def has( self, name ):
      return self.game_internal.has( name )

   def stuffs( self ):
      return self.game_internal.stuffs()

   def won( self ):
      return self.game_internal.won()

   # === Manipulating the game board ===

   def do_it( self, command, arg1, arg2 = '' ):
      if command == 'use':
         retval = self.game_internal.use( arg1, arg2 )
      elif command == 'drop':
         retval = self.game_internal.drop( arg1 )
      elif command == 'take':
         retval = self.game_internal.take( arg1 )
      elif command == 'go':
         retval = self.game_internal.go( arg1 )
      elif command == 'open':
         retval = self.game_internal.open( arg1 )
      else:
         raise Exception('Invalid command')
      self.game_internal.view_refresh()
      return retval

class GameInternal:
   def __init__( self, rooms, passages, use_actions, views, final_room ):
      self.rooms       = rooms
      if ( len(rooms) > 0 ):
         self.room        = rooms[0] 
      else:
         self.room        = None
      self.passages    = passages
      self.inventory   = GameObject( 'inventory', '', [], [] )
      self.use_actions = use_actions
      self.views       = views
      self.won_        = 0
      self.final_room  = final_room

   def setting_current_room( self, room_name ):
      self.room = self.find_room( room_name )
      if ( room_name == self.final_room ):
         self.winning()

   def move_between_entities( self, name, from_entity, to_entity ):
      subject = from_entity.take( name )
      if ( not subject is None ):
         if ( not to_entity is None ):
            to_entity.put( subject )
         return subject
      return None

   def view_refresh( self ):
      sorrounding_objects = [] + self.inventory.childObjects + self.room.childObjects
      for action in self.views:
         # cheating to make it faster
         subject, entity = self.find( action.subjectname )
         tool,    entity = self.find( action.toolname )
         if not subject is None and not tool is None and action.applicable( subject.name, tool.name ):
            action.showIt( self )

   def find_in_entities( self, name, entities ):
      for entity in entities:
         attempt = entity.find( name ) 
         if not attempt is None:
            return attempt, entity
      return None, None

   def find_room( self, name ):
      for room in self.rooms:
         if room.name == name:
            return room
      else:
         return None

   def open( self, name ):
      subject, entity = self.find( name )
      if subject is None:
         return False
      for child in subject.children(): 
         entity.put(subject.take( child.name ) )
      return True
         
   def use_internal( self, subjectname, toolname ):
      if subjectname == '':
         return None
      subject, entity = self.find( subjectname )
      if subject is None:
         return None
      if toolname == '':
         for action in self.use_actions:
            if action.applicable( subject.name, '' ):
               return action.doIt( self )
         return None
      else:
         tool = self.inventory.find( toolname )
         if ( tool is None ):
            return None
         for action in self.use_actions:
            if action.applicable( subject.name, tool.name ):
               return action.doIt( self )
         return None

   def take( self, name ):
      return self.move_between_entities( name, self.room, self.inventory )

   def drop( self, name ):
      return self.move_between_entities( name, self.inventory, self.room )

   def has( self, name ):
      subject = self.inventory.find( name )
      return subject

   def look( self ):
      return self.room.description

   def find( self, name ):
      return self.find_in_entities( name, [ self.inventory, self.room ] )

   def use( self, subjectname, toolname = '' ):
      retval = self.use_internal( subjectname, toolname )
      if ( not retval is None ):
         return retval
      return self.use_internal( toolname, subjectname )

   def directionsInternal( self, room_name, visibility = 1 ):
      retval = []
      for passage in self.passages:
         tmp = passage.get_out_passage_from_room(room_name, visibility)
         if not tmp is None:
            retval.append( tmp )
      return retval

   def find_path_between_rooms( self, endfunc, current_room = '', way = [], rooms = [] ):
      if current_room == '':
         return self.find_path_between_rooms( endfunc, self.room.name, way, rooms )
      if endfunc( current_room ):
         return way
      for [ direction, room_name ] in self.directionsInternal( current_room, 1 ):
         if not room_name in rooms:
            whatIfPath = self.find_path_between_rooms( endfunc, room_name, way + [ direction ], rooms + [ current_room ] )
            if not whatIfPath is None:
               return whatIfPath
      return None

   def accessible_room_names( self, first_room = '' ):
      # Preparations
      if ( len( self.rooms ) == 0 ):
         return []
      visited_room_names = []
      candidate_list = []
      if first_room == '':
         candidate_list.apped( self.room.name )
      else:
         candidate_list.append( first_room )

      # visiting rooms
      while len( candidate_list ) > 0:
         candidate = candidate_list.pop()
         if not candidate in visited_room_names:
            visited_room_names.append( candidate )
            for [i,j] in self.directionsInternal( candidate, 0 ):
               candidate_list.append( j )

      # retval
      return visited_room_names

   def can_anything_to_do( self, roomname ):
      myroom = self.find_room( roomname )
      return not self.applicable_uses( roomname ) == [] or not myroom.mobile_child_names() == [] or not myroom.openable_child_names() == []

   def applicable_uses( self, roomname = '' ):
      if roomname == '':
         myroom = self.room
      else:
         myroom = self.find_room( roomname )
         
      # toolname == ''
      subjectnames = []
      for child in self.room.children():
         if not GameObjectAttribute.INVISIBLE in child.attributes:
            subjectnames.append( child ) 
      for child in self.inventory.children():
         subjectnames.append( child )

      uses = []
      for subject in subjectnames:
         for action in self.use_actions:
            if action.applicable( subject.name, '' ):
               pair = action.get_actor_names()
               if not pair in uses:
                  uses.append( pair ) 
            if action.applicable( '', subject.name ):
               pair = action.get_actor_names()
               if not pair in uses:
                  uses.append( pair ) 
         for tool in self.inventory.children():
            for action in self.use_actions:
               if action.applicable( subject.name, tool.name ):
                  pair = action.get_actor_names()
                  if not pair in uses:
                     uses.append( pair ) 
               if action.applicable( tool.name, subject.name ):
                  pair = action.get_actor_names()
                  if not pair in uses:
                     uses.append( pair ) 

      return uses

   def directions( self ):
      return self.directionsInternal( self.room.name )

   def go( self, direction ):
      topology = self.directions()
      for [room_direction, room_name] in topology:
         if room_direction == direction:
            self.setting_current_room( room_name )
            return self.room
      return None  

   def stuffs( self ):
      retval = []
      for subject in self.room.children():
         if not GameObjectAttribute.INVISIBLE in subject.attributes:
            appearance = self.room.find( subject.name ) 
            if ( not appearance is None ):
               retval.append( appearance.name )
      return retval

   def winning( self ):
      self.won_ = 1

   def won( self ):
      return self.won_

class GameObjectUseAction:
   def __init__( self, subjectname, toolname, actionDescription, prototype ):
      self.subjectname       = subjectname
      self.toolname          = toolname
      self.actionDescription = actionDescription
      self.prototype         = prototype

   def is_brutal( self ):
      return True

   def get_prototype( self ):
      return [ copy.deepcopy( self.prototype ) ]

   def get_actor_names( self ):
      if self.subjectname < self.toolname:
         return [ self.subjectname, self.toolname ]
      else:
         return [ self.toolname, self.subjectname ]

   def applicable( self, subjectname, toolname ):
      return self.subjectname == subjectname and self.toolname == toolname

   def showIt( self, game ):
      game.views.remove( self )
      game.move_between_entities( self.toolname, game.inventory, None )
      subject, entity = game.find( self.subjectname )
      if not subject is None:
         entity.take( subject.name )
         retval = copy.deepcopy( self.prototype )
         entity.put( retval )
         return retval
      return None

   def doIt( self, game ):
      game.use_actions.remove( self )
      game.move_between_entities( self.toolname, game.inventory, None )
      subject, entity = game.find( self.subjectname )
      if not subject is None:
         entity.take( subject.name )
         retval = copy.deepcopy( self.prototype )
         entity.put( retval )
         return retval
      return None

class GamePassageRevealAction:
   def __init__( self, subjectname, toolname, actionDescription, identifier ):
      self.subjectname       = subjectname
      self.toolname          = toolname
      self.actionDescription = actionDescription
      self.identifier        = identifier

   def is_brutal( self ):
      return False

   def get_prototype( self ):
      return []

   def get_actor_names( self ):
      if self.subjectname < self.toolname:
         return [ self.subjectname, self.toolname ]
      else:
         return [ self.toolname, self.subjectname ]

   def get_passage_identifier( self ):
      return self.identifier

   def applicable( self, subjectname, toolname ):
      return self.subjectname == subjectname and self.toolname == toolname

   def showIt( self, game ):
      raise Exception('Cannot use passage action as a view, it modifies the world')
 
   def doIt( self, game ):
      for passage in game.passages:
         if passage.identifier == self.identifier:
            passage.make_visible()

class GameObjectRevealAction:
   def __init__( self, subjectname, toolname, actionDescription ):
      self.subjectname       = subjectname
      self.toolname          = toolname
      self.actionDescription = actionDescription

   def is_brutal( self ):
      return False

   def get_prototype( self ):
      return []

   def get_actor_names( self ):
      if self.subjectname < self.toolname:
         return [ self.subjectname, self.toolname ]
      else:
         return [ self.toolname, self.subjectname ]

   def get_passage_identifier( self ):
      return self.identifier

   def applicable( self, subjectname, toolname ):
      return self.subjectname == subjectname and self.toolname == toolname

   def showIt( self, game ):
      game.views.remove( self ) # optimization
      tool,    entity = game.find( self.toolname )
      subject, entity = game.find( self.subjectname )
      if not tool is None and not subject is None and not subject.is_visible():
         subject.make_visible()
         return subject
      return None
 
   def doIt( self, game ):
      raise Exception('Cannot use game object reveal action with use.')

class GameObjectAttribute:
   IMMOBILE  = 'immobile'
   INVISIBLE = 'invisible'

class GameObject:

   def __init__( self, name = '', description = '', attributes = [], cobs = []):
      self.name = name
      self.description  = description
      self.attributes   = attributes
      self.childObjects = cobs

   def make_equal_to( self, other ):
      self.name         = other.name
      self.description  = other.description
      self.childObjects = other.childObjects

   def is_visible( self ):
      if GameObjectAttribute.INVISIBLE in self.attributes:
         return False
      return True

   def make_visible( self ):
      if GameObjectAttribute.INVISIBLE in self.attributes:
         self.attributes.remove( GameObjectAttribute.INVISIBLE )

   def look( self ):
      return self.description

   def get_attributes( self ):
      return self.attributes

   # todo: refactor with take if you will be more experienced
   def find( self, name ):
      for child in self.childObjects:
         if child.name == name:
            return child
      return None

   def children( self ):
      return self.childObjects

   def mobile_child_names( self ):
      retval = []
      for child in self.childObjects:
         if not GameObjectAttribute.IMMOBILE in child.attributes:
            retval.append( child.name )
      return retval

   def openable_child_names( self ):
      retval = []
      for child in self.childObjects:
         if not child.childObjects == []:
            retval.append( child.name )
      return retval

   def descendants( self, add_top_children = 1 ):
      retval = []
      if add_top_children:
         retval += self.children()
      for child in self.children():
         retval += child.children()
      return retval

   def take( self, name ):
      for child in self.childObjects:
         if child.name == name and not GameObjectAttribute.IMMOBILE in child.attributes :
            self.childObjects.remove( child )
            return child
      return None 

   def put( self, child ):
      if not child is None:
         self.childObjects.append( child )

class GamePassage:
   def __init__( self, identifier, room_name1, room_name2, direction1, direction2, attributes = [] ):
      self.identifier = identifier
      self.room_name1 = room_name1
      self.room_name2 = room_name2
      self.direction1 = direction1
      self.direction2 = direction2
      self.attributes = attributes

   def get_ordered_name( self ):
      if ( self.room_name1 < self.room_name2 ):
         return [self.room_name1, self.room_name2]
      else:
         return [self.room_name2, self.room_name1]

   def make_visible( self ):
      self.attributes.remove( GameObjectAttribute.INVISIBLE )

   def get_out_passage_from_room( self, roomname, visibility = 1 ):
      if ( visibility and GameObjectAttribute.INVISIBLE in self.attributes ):
         return None
      else:
         if self.room_name1 == roomname:
            return [ self.direction1, self.room_name2 ]
         if self.room_name2 == roomname:
            return [ self.direction2, self.room_name1 ]

